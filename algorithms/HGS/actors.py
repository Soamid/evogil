import random
import uuid
from typing import Dict

from thespian.actors import Actor

from algorithms.HGS import tools
from algorithms.HGS.message import (
    NodeOperation,
    NodeMessage,
    HgsMessage,
    HgsOperation,
    Message,
)
from algorithms.HGS.node_tasks import (
    CheckStatusNodeTask,
    GetPopulationNodeTask,
    NewMetaepochNodeTask,
    TrimNotProgressingNodeTask,
    ReleaseSproutsNodeTask)
from algorithms.HGS.tasks import (
    HgsOperationTask,
    MetaepochHgsTask,
    TrimNotProgressingHgsTask,
    TrimRedundantHgsTask,
    StatusHgsTask,
    PopulationHgsTask,
    OperationTask,
    ReleaseSproutsHgsTask)


class HgsConfig:
    driver = None
    population = None
    population_sizes = None
    dims = None
    metaepoch_len = None
    fitnesses = None
    fitness_errors = None
    max_level = None
    max_sprouts_no = None
    sproutiveness = None
    mutation_etas = None
    mutation_rates = None
    crossover_etas = None
    crossover_rates = None
    cost_modifiers = None
    min_dists = None
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


class TaskActor(Actor):
    def __init__(self):
        super().__init__()
        self.tasks: Dict[uuid, OperationTask] = {}
        self.task_definitions = self.configure_tasks()

    def configure_tasks(self):
        raise NotImplementedError()

    def execute_new_task(self, msg: Message, sender: Actor):
        task = self.task_definitions[msg.operation](self)
        self.tasks[task.id] = task
        task.execute(msg, sender)


class HgsNodeSupervisor(TaskActor):
    def __init__(self):
        super().__init__()
        self.nodes = None
        self.level_nodes = None
        self.root = None
        self.config = None
        self.cost = 0
        self.tasks: Dict[uuid, HgsOperationTask] = {}

    def configure_tasks(self):
        return {
            HgsOperation.NEW_METAEPOCH: MetaepochHgsTask,
            HgsOperation.TRIM_NOT_PROGRESSING: TrimNotProgressingHgsTask,
            HgsOperation.TRIM_REDUNDANT: TrimRedundantHgsTask,
            HgsOperation.CHECK_STATUS: StatusHgsTask,
            HgsOperation.POPULATION: PopulationHgsTask,
            HgsOperation.RELEASE_SPROUTS: ReleaseSproutsHgsTask
        }

    def receiveMessage(self, msg, sender):
        print("SUPERVISOR RECEIVED: " + str(msg))
        if isinstance(msg, HgsMessage):
            if msg.operation == HgsOperation.START:
                self.start(msg.data)
                self.parent_actor = sender
                self.send(sender, "done")
            elif msg.operation == HgsOperation.REGISTER_NODE:
                node = self.create_node(msg.data.level, msg.data.population)
                self.nodes.append(node)
                self.level_nodes[msg.data.level].append(node)
                self.send(
                    sender, HgsMessage(HgsOperation.REGISTER_NODE_END, msg.id, node)
                )
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
        return self.create_node(
            0, random.sample(self.config.population, self.config.population_sizes[0])
        )

    def create_node(self, level, population):
        node = self.createActor(Node)
        # time.sleep(10)
        node_config = NodeConfig(self.config, level, population)
        self.send(node, HgsMessage(HgsOperation.HELLO))
        self.send(node, NodeMessage(NodeOperation.RESET, data=node_config))
        return node


class Node(TaskActor):
    alive = None
    ripe = None
    level = None
    min_dists = None
    max_level = None
    max_hgs_sprouts_no = None
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
    sproutiveness = None
    supervisor = None

    hgs_population_sizes = None
    hgs_dims = None
    hgs_mutation_rates = None
    hgs_mutation_etas = None

    def __init__(self):
        super().__init__()
        print("NODE CREATED")

    def configure_tasks(self):
        return {
            NodeOperation.CHECK_STATUS: CheckStatusNodeTask,
            NodeOperation.POPULATION: GetPopulationNodeTask,
            NodeOperation.NEW_METAEPOCH: NewMetaepochNodeTask,
            NodeOperation.TRIM_NOT_PROGRESSING: TrimNotProgressingNodeTask,
            NodeOperation.RELEASE_SPROUTS: ReleaseSproutsNodeTask
        }

    def receiveMessage(self, msg, sender):
        print("MESSAGE RECEIVED " + str(msg))
        if isinstance(msg, NodeMessage):
            if msg.operation == NodeOperation.RESET:
                self.reset(msg.data)
                self.send(sender, "done")
            else:
                self.execute_new_task(msg, sender)
        elif isinstance(msg, HgsMessage):
            if msg.operation == HgsOperation.HELLO:
                self.supervisor = sender

    def reset(self, config: NodeConfig):
        print("HAHA1")
        self.alive = True
        self.ripe = False
        self.level = config.level
        self.min_dists = config.hgs_config.min_dists
        self.max_level = config.hgs_config.max_level
        self.max_hgs_sprouts_no = config.hgs_config.max_sprouts_no
        self.sproutiveness = config.hgs_config.sproutiveness
        self.current_cost = 0
        self.hgs_population_sizes = config.hgs_config.population_sizes
        self.hgs_dims = config.hgs_config.dims
        self.hgs_mutation_rates = config.hgs_config.mutation_rates
        self.hgs_mutation_etas = config.hgs_config.mutation_etas
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
