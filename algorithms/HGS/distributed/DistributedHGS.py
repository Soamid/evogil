import logging

import numpy as np
from thespian.actors import ActorSystem, ActorExitRequest

from algorithms.HGS import tools
from algorithms.HGS.distributed.actors import HgsNodeSupervisor, HgsConfig
from algorithms.HGS.distributed.message import HgsMessage, HgsOperation
from algorithms.base.driver import ComplexDriver
from simulation import log_helper

EPSILON = np.finfo(float).eps

logger = logging.getLogger(__name__)



class DistributedHGS(ComplexDriver):
    def __init__(
            self,
            population,
            dims,
            fitnesses,
            fitness_errors,
            cost_modifiers,
            driver,
            mutation_etas,
            crossover_etas,
            mutation_rates,
            crossover_rates,
            reference_point,
            mantissa_bits,
            min_progress_ratio,
            metaepoch_len=5,
            max_level=2,
            max_sprouts_no=20,
            sproutiveness=1,
            comparison_multipliers=(1.0, 0.1, 0.01),
            population_sizes=(64, 16, 4),
            *args,
            **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.hgs_config = HgsConfig()

        self.hgs_config.driver = driver
        self.hgs_config.population = population

        self.hgs_config.dims = dims
        self.hgs_config.reference_point = reference_point
        self.hgs_config.fitnesses = fitnesses

        self.hgs_config.fitness_errors = fitness_errors
        self.hgs_config.cost_modifiers = cost_modifiers

        corner_a = np.array([x for x, _ in dims])
        corner_b = np.array([x for _, x in dims])
        corner_dist = np.linalg.norm(corner_a - corner_b)
        self.hgs_config.min_dists = [x * corner_dist for x in comparison_multipliers]
        logger.info(f'multipliers: {comparison_multipliers}, min dists: {self.hgs_config.min_dists}')

        self.hgs_config.metaepoch_len = metaepoch_len
        self.hgs_config.max_level = max_level
        self.hgs_config.max_sprouts_no = max_sprouts_no
        self.hgs_config.sproutiveness = sproutiveness
        self.hgs_config.min_progress_ratio = min_progress_ratio

        self.hgs_config.mutation_etas = mutation_etas
        self.hgs_config.mutation_rates = mutation_rates
        self.hgs_config.crossover_etas = crossover_etas
        self.hgs_config.crossover_rates = crossover_rates
        self.hgs_config.population_sizes = population_sizes

        self.hgs_config.mantissa_bits = mantissa_bits
        self.hgs_config.driver_message_adapter_factory = (
            self.driver_message_adapter_factory
        )

        # TODO this is shared variable which is a problem in actor model
        self.hgs_config.global_fitness_archive = [
            tools.ResultArchive() for _ in range(3)
        ]

        # TODO add preconditions checking if message adapter is HGS message adapter

        logger.info("HGS CREATED")
        self.hgs_system = ActorSystem()
        self.node_supervisor = self.hgs_system.createActor(HgsNodeSupervisor)

        self.hgs_system.ask(
            self.node_supervisor, HgsMessage(HgsOperation.START, data=self.hgs_config)
        )
        self.hgs_system.ask(
            self.node_supervisor, HgsMessage(HgsOperation.CHECK_STATUS)
        )
        self.cost = 0

    def shutdown(self):
        self.hgs_system.tell(self.node_supervisor, ActorExitRequest())

    def finalized_population(self):
        return (
            ActorSystem()
                .ask(self.node_supervisor, HgsMessage(HgsOperation.POPULATION))
                .data
        )

    def step(self):
        epoch_end_message = ActorSystem().ask(
            self.node_supervisor, HgsMessage(HgsOperation.NEW_METAEPOCH)
        )
        self.cost = epoch_end_message.data

        ActorSystem().ask(
            self.node_supervisor, HgsMessage(HgsOperation.TRIM_NOT_PROGRESSING)
        )
        ActorSystem().ask(self.node_supervisor, HgsMessage(HgsOperation.TRIM_REDUNDANT))
        ActorSystem().ask(
            self.node_supervisor, HgsMessage(HgsOperation.RELEASE_SPROUTS)
        )

        ActorSystem().ask(
            self.node_supervisor, HgsMessage(HgsOperation.REVIVE)
        )
        logger.info(f"step finished, current cost = {self.cost}")