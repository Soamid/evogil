import itertools
import logging
import random

import rx
import rx.operators as ops
from rx.concurrency import NewThreadScheduler

from algorithms.IMGA.topology import TorusTopology, Topology
from algorithms.base.driver import StepsRun, ComplexDriver
from evotools import ea_utils
from evotools.random_tools import weighted_choice


class IMGA(ComplexDriver):
    def __init__(self,
                 population,
                 dims,
                 fitnesses,
                 islands_number,
                 migrants_number,
                 epoch_length,
                 driver,
                 mutation_eta,
                 crossover_eta,
                 mutation_rate,
                 crossover_rate,
                 topology=TorusTopology(4),
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fitnesses = fitnesses
        self.dims = dims
        self.mutation_eta = mutation_eta
        self.mutation_rate = mutation_rate
        self.crossover_eta = crossover_eta
        self.crossover_rate = crossover_rate

        self.islands_number = islands_number
        self.migrants_number = migrants_number
        self.epoch_length = epoch_length
        self.topology = topology.create(islands_number)
        self.driver = driver
        self.total_cost = 0

        self.islands = self.create_islands(population)
        self.epoch_no = 0

        Topology.print(self.topology)

        self.logger = logging.getLogger(__name__)

        self.spread_budget_info()

    def spread_budget_info(self):
        if self.max_budget:
            for island in self.islands:
                island.driver.max_budget = self.max_budget

    def finalized_population(self):
        return itertools.chain(*(island.driver.finalized_population() for island in self.islands))

    def step(self):
        last_result = rx.from_iterable(self.islands).pipe(
            ops.subscribe_on(NewThreadScheduler()),
            ops.flat_map(lambda island: island.epoch(self.epoch_length).pipe(ops.last())),
            ops.buffer_with_count(len(self.islands))
        ).run()
        self.migration()
        self.update_cost(last_result)

    def update_cost(self, results):
        self.cost = sum(result.cost for result in results)

    def migration(self):
        for i in range(len(self.islands)):
            island = self.islands[i]

            for n in self.topology[i]:
                self.islands[n].immigrate(island.emigrate())
        for island in self.islands:
            island.assimilate()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def create_islands(self, init_population):
        logger = logging.getLogger(__name__)
        subpop_size = int(len(init_population) / self.islands_number)

        subpopulations = [init_population[i * subpop_size:(i + 1) * subpop_size] for i in range(self.islands_number)]

        for i in range(len(init_population) % self.islands_number):
            subpopulations[i].append(init_population[self.islands_number * subpop_size + i])

        logger.debug(subpopulations)

        return [IMGA.Island(self, subpop) for subpop in subpopulations]

    class Island:

        def __init__(self,
                     outer,
                     population):
            self.outer = outer
            self.population = population

            self.driver = outer.driver(population=population,
                                       dims=outer.dims,
                                       fitnesses=outer.fitnesses,
                                       mutation_rate=outer.mutation_rate,
                                       mutation_eta=outer.mutation_eta,
                                       crossover_rate=outer.crossover_rate,
                                       crossover_eta=outer.crossover_eta,
                                       message_adapter_factory=outer.driver_message_adapter_factory
                                       )
            self.visa_office = []
            self.all_refugees = []

        def epoch(self, epoch_length):
            steps_run = StepsRun(epoch_length)
            return steps_run.create_job(self.driver)

        def finish(self):
            return self.driver.finish()

        def emigrate(self):
            logger = logging.getLogger(__name__)

            def fitfun_res(ind):
                return [f(ind) for f in self.outer.fitnesses]

            current_population = self.driver.population

            refugees = []
            for _ in range(self.outer.migrants_number):
                pareto_layers = [l for l in ea_utils.paretofront_layers(current_population, fitfun_res=fitfun_res)]

                weights = [1 / (i + 1) for i in range(len(pareto_layers))]

                chosen_layer = weighted_choice(zip(pareto_layers, weights))

                refugee = random.choice(chosen_layer)
                refugees.append(refugee)
                if refugee not in current_population:
                    logger.error("DUPA WSZECHCZASÓW")
                current_population.remove(refugee)

            logger.debug('after emigrate: ' + str(len(self.driver.population)))

            self.all_refugees.extend(refugees)
            return self.driver.message_adapter.emigrate(refugees)

        def immigrate(self, migrants):
            self.visa_office.extend(migrants)

        def assimilate(self):
            logger = logging.getLogger(__name__)
            if len(self.visa_office) != len(self.all_refugees):
                raise ValueError(
                    'Number of immigrants and emigrants should be equal: {} != {}'.format(len(self.visa_office),
                                                                                          len(self.all_refugees)))

            self.driver.message_adapter.immigrate(self.visa_office)
            logger.debug('after immigrate: ' + str(len(self.driver.population)))

            self.all_refugees.clear()
            self.visa_office.clear()
