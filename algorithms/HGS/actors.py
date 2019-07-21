import random
import uuid
from typing import Dict

import numpy as np
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
    CheckStatusTask,
    GetPopulationTask,
    NewMetaepochTask,
    TrimNotProgressing,
    NodeOperationTask)
from algorithms.HGS.tasks import (
    HgsOperationTask,
    MetaepochTask,
    TrimNotProgressingTask,
    TrimRedundantTask,
    StatusTask,
    PopulationTask,
    OperationTask,
)


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
        self.config = None
        self.cost = 0
        self.tasks: Dict[uuid, HgsOperationTask] = {}

    def configure_tasks(self):
        return {
            HgsOperation.NEW_METAEPOCH: MetaepochTask,
            HgsOperation.TRIM_NOT_PROGRESSING: TrimNotProgressingTask,
            HgsOperation.TRIM_REDUNDANT: TrimRedundantTask,
            HgsOperation.CHECK_STATUS: StatusTask,
            HgsOperation.POPULATION: PopulationTask,
        }

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


class Node(TaskActor):
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
        super().__init__()
        print("NODE CREATED")

    def configure_tasks(self):
        return {
            NodeOperation.CHECK_STATUS: CheckStatusTask,
            NodeOperation.POPULATION: GetPopulationTask,
            NodeOperation.NEW_METAEPOCH: NewMetaepochTask,
            NodeOperation.TRIM_NOT_PROGRESSING: TrimNotProgressing,
        }

    def receiveMessage(self, msg, sender):
        print("MESSAGE RECEIVED " + str(msg))
        if isinstance(msg, NodeMessage):
            if msg.operation == NodeOperation.RESET:
                self.reset(msg.data)
                self.send(sender, "done")
            else:
                self.execute_new_task(msg, sender)

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
