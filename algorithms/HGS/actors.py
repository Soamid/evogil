import random

import rx
import rx.operators as ops
from rx import Observable
from thespian.actors import Actor

from algorithms.HGS import tools
from algorithms.HGS.message import NodeOperation, NodeMessage, HgsMessage, HgsOperation
from algorithms.base.driver import StepsRun
from algorithms.base.hv import HyperVolume


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
    global_fitness_archive = None
    mantissa_bits = None
    driver_message_adapter_factory = None
    reference_point = None


class NodeConfig:
    def __init__(self, hgs_config: HgsConfig, level: int, population):
        self.hgs_config = hgs_config
        self.level = level
        self.population = population


class HgsNodeSupervisor(Actor):
    def __init__(self):
        self.nodes = None
        self.level_nodes = None
        self.config = None
        self.nodes_states = []
        self.merged_population = []
        self.nodes_calculating = 0
        self.cost = 0

    def receiveMessage(self, msg, sender):
        print("SUPERVISOR RECEIVED: " + str(msg))
        if isinstance(msg, HgsMessage):
            if msg.operation == HgsOperation.START:
                self.start(msg.data)
                self.parent_actor = sender
                self.send(sender, "done")
            elif msg.operation == HgsOperation.NEW_METAEPOCH:
                self.run_metaepoch()
            elif msg.operation == HgsOperation.CHECK_ALL_ALIVE:
                self.nodes_states = []
                for node in self.nodes:
                    self.send(node, NodeMessage(NodeOperation.CHECK_ALIVE))
            elif msg.operation == HgsOperation.POPULATION:
                for node in self.nodes:
                    self.merged_population = []
                    self.nodes_calculating = 0
                    self.send(node, NodeMessage(NodeOperation.POPULATION))

        elif isinstance(msg, NodeMessage):
            if msg.operation == NodeOperation.CHECK_ALIVE:
                self.nodes_states.append(msg.data)
                if len(self.nodes_states) == len(self.nodes):
                    self.send(self.parent_actor, self.nodes_states)
            elif msg.operation == NodeOperation.NEW_RESULT:
                self._update_cost(msg.data)
            elif msg.operation == NodeOperation.METAEPOCH_END:
                self.nodes_calculating += 1
                if self.nodes_calculating == len(self.nodes):
                    print("All nodes have ended their metaepochs")
                    self.send(
                        self.parent_actor,
                        HgsMessage(HgsOperation.METAEPOCH_END, self.cost),
                    )
            elif msg.operation == NodeOperation.POPULATION:
                self.merged_population.extend(msg.data)
                self.nodes_calculating += 1
                if self.nodes_calculating == len(self.nodes):
                    self.send(
                        self.parent_actor,
                        HgsMessage(HgsOperation.POPULATION, self.merged_population),
                    )


    def _update_cost(self, message):
        print("update cost")
        self.cost += self.config.cost_modifiers[message.level] * message.epoch_cost

    def start(self, config: HgsConfig):
        print("STARTING HGS SUPERVISOR")
        self.config = config
        self.root = self.create_root_node()
        print("ROOT CREATED")
        self.nodes = [self.root]
        self.level_nodes = {0: [self.root], 1: [], 2: []}

    def create_root_node(self):
        root = self.createActor(Node)
        self.send(root, "is_alive")
        # time.sleep(10)
        root_config = NodeConfig(
            self.config,
            0,
            random.sample(self.config.population, self.config.population_sizes[0]),
        )
        self.send(root, NodeMessage(NodeOperation.RESET, root_config))
        return root

    def run_metaepoch(self):
        self.nodes_calculating = 0
        for node in self.nodes:
            self.send(node, NodeMessage(NodeOperation.NEW_METAEPOCH))


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
    reference_point = None
    relative_hypervolume = None
    old_hypervolume = None
    hypervolume = None

    def __init__(self):
        print("NODE CREATED")

    def receiveMessage(self, msg, sender):
        print("MESSAGE RECEIVED " + str(msg))
        if isinstance(msg, NodeMessage):
            if msg.operation == NodeOperation.RESET:
                self.reset(msg.data)
                self.send(sender, "done")
            elif msg.operation == NodeOperation.CHECK_ALIVE:
                self.send(sender, NodeMessage(NodeOperation.CHECK_ALIVE, self.alive))
            elif msg.operation == NodeOperation.CHECK_RIPE:
                self.send(sender, self.ripe)
            elif msg.operation == NodeOperation.NEW_METAEPOCH:
                self.run_metaepoch().pipe(
                    ops.do_action(
                        on_completed=lambda: self.send(
                            sender, NodeMessage(NodeOperation.METAEPOCH_END)
                        )
                    )
                ).subscribe(
                    lambda result: self.send(
                        sender, NodeMessage(NodeOperation.NEW_RESULT, result)
                    )
                )
            elif msg.operation == NodeOperation.POPULATION:
                self.send(sender, NodeMessage(NodeOperation.POPULATION, self.population))

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
