import itertools
import logging
import random

from rx import Observable

from algorithms.IMGA.topology import TorusTopology, Topology
from algorithms.base.drivergen import DriverGen, ImgaProxy, Driver, StepsRun, DriverRxWrapper, DriverRx
from evotools import ea_utils
from evotools.random_tools import weighted_choice


class IMGA(DriverRx):
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
                 topology=TorusTopology(4)):
        super().__init__()
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

    class IMGAImgaProxy(ImgaProxy):
        def __init__(self, driver, cost, results):
            super().__init__(driver, cost)
            self.global_population = results

        def finalized_population(self):
            return self.global_population

        def current_population(self):
            return self.finalized_population()

        def deport_emigrants(self, immigrants):
            raise Exception("IMGA does not support migrations")

        def assimilate_immigrants(self, emigrants):
            raise Exception("IMGA does not support migrations")

        def nominate_delegates(self):
            raise Exception("IMGA does not support migrations")

    def spread_budget_info(self):
        if self.max_budget:
            for island in self.islands:
                island.driver.max_budget = self.max_budget

    def steps(self):
        return Observable.merge([island.steps() for island in self.islands]) \
            .filter(lambda proxy: proxy.step_no % self.epoch_length == 0) \
            .buffer_with_count(len(self.islands)) \
            .do_action(lambda _: self.migration()) \
            .map(self.create_proxy)

    def create_proxy(self, island_proxies):
        self.cost = sum(proxy.cost for proxy in island_proxies)
        all_results = itertools.chain(*(proxy.finalized_population() for proxy in island_proxies))
        return IMGA.IMGAImgaProxy(self, self.cost, list(all_results))

    def step(self):
        for island in self.islands:
            island.epoch(self.epoch_length)
            # TODO return hot observable results


    def migration(self):
        for i in range(len(self.islands)):
            island = self.islands[i]

            for n in self.topology[i]:
                self.islands[n].immigrate(island.emigrate())
        for island in self.islands:
            island.assimilate()

    def create_islands(self, init_population):
        logger = logging.getLogger(__name__)
        subpop_size = int(len(init_population) / self.islands_number)

        subpopulations = [init_population[i * subpop_size:(i + 1) * subpop_size] for i in range(self.islands_number)]

        for i in range(len(init_population) % self.islands_number):
            subpopulations[i].append(init_population[self.islands_number * subpop_size + i])

        logger.debug(subpopulations)

        return [IMGA.Island(self, subpop) for subpop in subpopulations]

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    class Island(DriverRx):

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
                                                       crossover_eta=outer.crossover_eta)
            self.driver_rx = DriverRxWrapper(self.driver)

            if isinstance(self.driver, DriverGen):
                self.driver_gen = self.driver.population_generator()
                self.last_proxy = None
            self.visa_office = []
            self.all_refugees = []

        def steps(self):
            return self.driver_rx.steps()

        def step(self):
            return self.driver_rx.step()

        def epoch(self, epoch_length):
            steps_run = StepsRun(epoch_length)
            steps_run.start(self.driver_rx)

        def finish(self):
            if isinstance(self.driver, DriverGen):
                return self.last_proxy.finalized_population()
            return self.driver.finish()

        def emigrate(self):
            logger = logging.getLogger(__name__)

            def fitfun_res(ind):
                return [f(ind) for f in self.outer.fitnesses]

            if isinstance(self.driver, DriverGen):
                current_population = self.last_proxy.current_population()
            else:
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

            if isinstance(self.driver, DriverGen):
                return self.last_proxy.deport_emigrants(refugees)
            else:
                self.driver.population = current_population
                return refugees

        def immigrate(self, migrants):
            self.visa_office.extend(migrants)

        def assimilate(self):
            logger = logging.getLogger(__name__)
            if len(self.visa_office) != len(self.all_refugees):
                raise ValueError(
                    'Number of immigrants and emigrants should be equal: {} != {}'.format(len(self.visa_office),
                                                                                          len(self.all_refugees)))

            if isinstance(self.driver, DriverGen):
                self.last_proxy.assimilate_immigrants(self.visa_office)
            else:
                current_population = self.driver.population
                current_population.extend(self.visa_office)
                self.driver.population = current_population

            logger.debug('after immigrate: ' + str(len(self.driver.population)))

            self.all_refugees.clear()
            self.visa_office.clear()
