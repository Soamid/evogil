import random
import uuid
from typing import Callable, Dict, Any

import numpy as np
import rx
import rx.operators as ops
from rx import Observable
from thespian.actors import Actor

from algorithms.HGS import tools
from algorithms.HGS.message import (
    NodeOperation,
    NodeMessage,
    HgsMessage,
    HgsOperation,
    OperationType,
    Message,
)
from algorithms.base.driver import StepsRun
from algorithms.base.hv import HyperVolume


EPSILON = np.finfo(float).eps


class HgsConfig:
    driver = None
    population = None
    population_sizes = None
    dims = None
    metaepoch_len = None
    fitnesses = None
    fitness_errors = None
    mutation_etas = None
    mutation_rates = None
    crossover_etas = None
    crossover_rates = None
    cost_modifiers = None
    min_progress_ratio = None
    global_fitness_archive = None
    mantissa_bits = None
    driver_message_adapter_factory = None
    reference_point = None


class NodeConfig:
    def __init__(self, hgs_config: HgsConfig, level: int, population):
        self.hgs_config = hgs_config
        self.level = level
        self.population = population


class OperationSteps:
    def __init__(self, hgs_supervisor):
        self.id = uuid.uuid4()
        self.hgs_supervisor = hgs_supervisor
        self.steps = {}
        self.configure_steps(self.steps)

    def configure_steps(self, steps: Dict[OperationType, Callable]):
        raise NotImplementedError()

    def execute(self, message: Message, sender: Actor):
        self.steps[message.operation](message.data, sender)


class MetaepochSteps(OperationSteps):
    def __init__(self, hgs_supervisor):
        super().__init__(hgs_supervisor)
        self.nodes_finished = 0

    def configure_steps(self, steps: Dict[OperationType, Callable]):
        steps[HgsOperation.NEW_METAEPOCH] = self.start_metaepoch
        steps[NodeOperation.NEW_RESULT] = self.on_new_result
        steps[NodeOperation.METAEPOCH_END] = self.finish_metaepoch

    def start_metaepoch(self, params: Any, sender: Actor):
        for node in self.hgs_supervisor.nodes:
            self.hgs_supervisor.send(
                node, NodeMessage(NodeOperation.NEW_METAEPOCH, self.id)
            )

    def on_new_result(self, params: Any, sender: Actor):
        print("update cost")
        self.hgs_supervisor.cost += (
            self.hgs_supervisor.config.cost_modifiers[params.level] * params.epoch_cost
        )

    def finish_metaepoch(self, params: Any, sender: Actor):
        self.nodes_finished += 1
        if self.nodes_finished == len(self.hgs_supervisor.nodes):
            print("All nodes have ended their metaepochs")
            self.hgs_supervisor.send(
                self.hgs_supervisor.parent_actor,
                HgsMessage(HgsOperation.METAEPOCH_END, self.hgs_supervisor.cost),
            )


class StatusSteps(OperationSteps):
    def __init__(self, hgs_supervisor):
        super().__init__(hgs_supervisor)
        self.nodes_states = []

    def configure_steps(self, steps: Dict[OperationType, Callable]):
        steps[HgsOperation.CHECK_STATUS] = self.send_check
        steps[NodeOperation.CHECK_STATUS] = self.finish_check

    def send_check(self, params: Any, sender: Actor):
        for node in self.hgs_supervisor.nodes:
            self.hgs_supervisor.send(
                node, NodeMessage(NodeOperation.CHECK_STATUS, self.id)
            )

    def finish_check(self, params: Any, sender: Actor):
        self.nodes_states.append(params)
        if len(self.nodes_states) == len(self.hgs_supervisor.nodes):
            self.hgs_supervisor.send(
                self.hgs_supervisor.parent_actor, self.nodes_states
            )


class PopulationSteps(OperationSteps):
    def __init__(self, hgs_supervisor):
        super().__init__(hgs_supervisor)
        self.merged_population = []
        self.nodes_finished = 0

    def configure_steps(self, steps: Dict[OperationType, Callable]):
        steps[HgsOperation.POPULATION] = self.get_nodes_populations
        steps[NodeOperation.POPULATION] = self.receive_population

    def get_nodes_populations(self, params: Any, sender: Actor):
        for node in self.hgs_supervisor.nodes:
            self.hgs_supervisor.send(
                node, NodeMessage(NodeOperation.POPULATION, self.id)
            )

    def receive_population(self, params: Any, sender: Actor):
        self.merged_population.extend(params)
        self.nodes_finished += 1
        if self.nodes_finished == len(self.hgs_supervisor.nodes):
            self.send_merged_population()

    def send_merged_population(self):
        self.hgs_supervisor.send(
            self.hgs_supervisor.parent_actor,
            HgsMessage(HgsOperation.POPULATION, self.merged_population),
        )


class TrimNotProgressingSteps(OperationSteps):
    def __init__(self, hgs_supervisor):
        super().__init__(hgs_supervisor)

    def configure_steps(self, steps: Dict[OperationType, Callable]):
        steps[HgsOperation.TRIM_NOT_PROGRESSING] = self.send_trim_request

    def send_trim_request(self, params: Any, sender: Actor):
        for node in self.hgs_supervisor.nodes:
            self.hgs_supervisor.send(
                node, NodeMessage(NodeOperation.TRIM_NOT_PROGRESSING, self.id)
            )


class TrimRedundantSteps(OperationSteps):
    def __init__(self, hgs_supervisor):
        super().__init__(hgs_supervisor)
        self.trim_infos = []

    def configure_steps(self, steps: Dict[OperationType, Callable]):
        steps[HgsOperation.TRIM_REDUNDANT] = self.send_trim_request
        steps[NodeOperation.TRIM_REDUNDANT] = self.receive_trim_confirmation

    def send_trim_request(self, params: Any, sender: Actor):
        for node in self.hgs_supervisor.nodes:
            self.hgs_supervisor.send(
                node, NodeMessage(NodeOperation.TRIM_REDUNDANT, self.id)
            )

    def receive_trim_confirmation(self, params: Any, sender: Actor):
        self.trim_infos.append({"node": sender, **params})
        if len(self.trim_infos) == len(self.hgs_supervisor.nodes):
            self.trim_redundant()
            self.hgs_supervisor.send(
                self.hgs_supervisor.parent_actor,
                HgsMessage(HgsOperation.TRIM_REDUNDANT, True),
            )

    def trim_redundant(self):
        alive = [x for x in self.trim_infos if x["alive"]]
        processed = []
        dead = [x for x in self.trim_infos if not x["alive"]]
        for sprout in alive:
            to_compare = [x for x in dead]
            to_compare.extend(processed)
            for another_sprout in to_compare:
                if not sprout["alive"]:
                    break
                if (
                    another_sprout["ripe"] or another_sprout in processed
                ) and tools.redundant(
                    [another_sprout["center"]],
                    [sprout["center"]],
                    self.hgs_supervisor.min_dists[sprout["level"]],
                ):
                    self.hgs_supervisor.send(
                        sprout["node"], NodeMessage(NodeOperation.KILL, self.id)
                    )
                    sprout["alive"] = False
                    # TODO: logging killing redundant sprouts
                    print("   KILL REDUNDANT")
            processed.append(sprout)


class HgsNodeSupervisor(Actor):
    def __init__(self):
        super().__init__()
        self.nodes = None
        self.level_nodes = None
        self.config = None
        self.cost = 0
        self.tasks: Dict[uuid, OperationSteps] = {}

        self.task_definitions = {
            HgsOperation.NEW_METAEPOCH: MetaepochSteps,
            HgsOperation.TRIM_NOT_PROGRESSING: TrimNotProgressingSteps,
            HgsOperation.TRIM_REDUNDANT: TrimRedundantSteps,
            HgsOperation.CHECK_STATUS: StatusSteps,
            HgsOperation.POPULATION: PopulationSteps,
        }

    def execute_new_task(self, msg: HgsMessage, sender: Actor):
        task = self.task_definitions[msg.operation](self)
        self.tasks[task.id] = task
        task.execute(msg, sender)

    def receiveMessage(self, msg, sender):
        print("SUPERVISOR RECEIVED: " + str(msg))
        if isinstance(msg, HgsMessage):
            if msg.operation == HgsOperation.START:
                self.start(msg.data)
                self.parent_actor = sender
                self.send(sender, "done")
            else:
                self.execute_new_task(msg, sender)

        elif isinstance(msg, NodeMessage):
            operation = self.tasks[msg.id]
            operation.execute(msg, sender)

    def start(self, config: HgsConfig):
        print("STARTING HGS SUPERVISOR")
        self.config = config
        self.root = self.create_root_node()
        print("ROOT CREATED")
        self.nodes = [self.root]
        self.level_nodes = {0: [self.root], 1: [], 2: []}

    def create_root_node(self):
        root = self.createActor(Node)
        # time.sleep(10)
        root_config = NodeConfig(
            self.config,
            0,
            random.sample(self.config.population, self.config.population_sizes[0]),
        )
        self.send(root, NodeMessage(NodeOperation.RESET, None, root_config))
        return root


class NodeState:
    def __init__(self, alive, ripe):
        self.alive = alive
        self.ripe = ripe


class Node(Actor):
    alive = None
    ripe = None
    level = None
    current_cost = None
    driver = None
    metaepoch_len = None
    population = None
    sprouts = None
    delegates = None
    fitnesses = None
    old_average_fitnesses = None
    average_fitnesses = None
    min_progress_ratio = None
    reference_point = None
    relative_hypervolume = None
    old_hypervolume = None
    hypervolume = None
    center = None

    def __init__(self):
        print("NODE CREATED")

    def receiveMessage(self, msg, sender):
        print("MESSAGE RECEIVED " + str(msg))
        if isinstance(msg, NodeMessage):
            if msg.operation == NodeOperation.RESET:
                self.reset(msg.data)
                self.send(sender, "done")
            elif msg.operation == NodeOperation.CHECK_STATUS:
                self.send(
                    sender,
                    NodeMessage(
                        NodeOperation.CHECK_STATUS,
                        msg.id,
                        NodeState(self.alive, self.ripe),
                    ),
                )
            elif msg.operation == NodeOperation.NEW_METAEPOCH:
                self.run_metaepoch().pipe(
                    ops.do_action(
                        on_completed=lambda: self.send(
                            sender, NodeMessage(NodeOperation.METAEPOCH_END, msg.id)
                        )
                    )
                ).subscribe(
                    lambda result: self.send(
                        sender, NodeMessage(NodeOperation.NEW_RESULT, msg.id, result)
                    )
                )
            elif msg.operation == NodeOperation.TRIM_NOT_PROGRESSING:
                self.trim_not_progressing()
            elif msg.operation == NodeOperation.TRIM_REDUNDANT:
                center = np.mean(self.population, axis=0)
                self.send(
                    sender,
                    NodeMessage(
                        NodeOperation.TRIM_REDUNDANT,
                        msg.id,
                        {
                            "alive": self.alive,
                            "ripe": self.ripe,
                            "center": center,
                            "level": self.level,
                        },
                    ),
                )
            elif msg.operation == NodeOperation.POPULATION:
                self.send(
                    sender,
                    NodeMessage(NodeOperation.POPULATION, msg.id, self.population),
                )

    def reset(self, config: NodeConfig):
        print("HAHA1")
        self.alive = True
        self.ripe = False
        self.level = config.level
        self.current_cost = 0
        self.driver = config.hgs_config.driver(
            population=config.population,
            dims=config.hgs_config.dims,
            fitnesses=tools.blurred_fitnesses(
                self.level,
                config.hgs_config.fitnesses,
                config.hgs_config.fitness_errors,
            ),
            mutation_eta=config.hgs_config.mutation_etas[self.level],
            mutation_rate=config.hgs_config.mutation_rates[self.level],
            crossover_eta=config.hgs_config.crossover_etas[self.level],
            crossover_rate=config.hgs_config.crossover_rates[self.level],
            # fitness_archive=config.global_fitness_archive,
            trim_function=lambda x: tools.trim_vector(
                x, config.hgs_config.mantissa_bits[self.level]
            ),
            message_adapter_factory=config.hgs_config.driver_message_adapter_factory,
        )
        print("HAHA " + str(type(self.driver)))
        self.metaepoch_len = config.hgs_config.metaepoch_len
        self.population = []
        self.sprouts = []
        self.delegates = []

        self.fitnesses = config.hgs_config.fitnesses
        self.old_average_fitnesses = [float("inf") for _ in config.hgs_config.fitnesses]
        self.average_fitnesses = [float("inf") for _ in config.hgs_config.fitnesses]
        self.min_progress_ratio = config.hgs_config.min_progress_ratio[self.level]

        self.reference_point = config.hgs_config.reference_point
        self.relative_hypervolume = None
        self.old_hypervolume = float("-inf")
        self.hypervolume = float("-inf")

    def run_metaepoch(self) -> Observable:
        if self.alive:
            print("ALIVE SO RUN EPOCH")
            epoch_job = StepsRun(self.metaepoch_len)

            return epoch_job.create_job(self.driver).pipe(
                ops.map(lambda message: self.fill_node_info(message)),
                ops.do_action(lambda message: self.update_current_cost(message)),
                ops.do_action(on_completed=lambda: self._after_metaepoch()),
            )
        print("DEAD SO EMPTY MSG")
        return rx.empty()

    def fill_node_info(self, driver_message):
        driver_message.level = self.level
        driver_message.epoch_cost = driver_message.cost - self.current_cost
        return driver_message

    def update_current_cost(self, driver_message):
        self.current_cost = driver_message.cost

    def _after_metaepoch(self):
        self.population = self.driver.finalized_population()
        self.delegates = self.driver.message_adapter.nominate_delegates()
        random.shuffle(self.delegates)
        self.update_dominated_hypervolume()

    def update_dominated_hypervolume(self):
        self.old_hypervolume = self.hypervolume
        fitness_values = [[f(p) for f in self.fitnesses] for p in self.population]
        hv = HyperVolume(self.reference_point)

        if self.relative_hypervolume is None:
            self.relative_hypervolume = hv.compute(fitness_values)
        else:
            self.hypervolume = hv.compute(fitness_values) - self.relative_hypervolume

    def trim_not_progressing(self):
        if (
            self.alive
            and self.old_hypervolume is not None
            and self.old_hypervolume > 0.0
            and ((self.hypervolume / (self.old_hypervolume + EPSILON)) - 1.0)
            < (self.min_progress_ratio / 2 ** self.level)
        ):
            # TODO: kij wie, czy współczynnik kurczący wymagany progress jest potrzebny (to / X**sprout.level)
            self.alive = False
            self.center = np.mean(self.population, axis=0)
            self.ripe = True
            # TODO: logging killing not progressing sprouts
            print("   KILL NOT PROGRESSING")
