import logging
import random

from algorithms.IMGA.topology import TorusTopology, Topology
from algorithms.base.drivergen import DriverGen
from algorithms.base.driverlegacy import DriverLegacy
from evotools import ea_utils
from evotools.random_tools import weighted_choice


class IMGA(DriverLegacy):
    def __init__(self,
                 population,
                 dims,
                 fitnesses,
                 mutation_variance,
                 crossover_variance,
                 islands_number,
                 migrants_number,
                 epoch_length,
                 driver,
                 topology=TorusTopology(4)):
        super().__init__(population, dims, fitnesses, mutation_variance, crossover_variance)
        self.islands_number = islands_number
        self.migrants_number = migrants_number
        self.epoch_length = epoch_length
        self.topology = topology.create(islands_number)
        self.driver = driver
        self.cost = 0

        self.islands = self.create_islands(population)
        self.epoch_no = 0

        Topology.print(self.topology)

    def steps(self, _iterator, budget=None):
        logger = logging.getLogger(__name__)
        for _ in _iterator:
            logger.debug(self.epoch_no)
            self.epoch_no += 1

            self.cost += self.epoch()
            if budget and self.cost > budget:
                break

        return self.cost

    @property
    def population(self):
        self.finished = True
        return self.finish()

    def finish(self):
        global_pop = []
        for pop in [island.finish() for island in self.islands]:
            global_pop.extend(pop)

        return global_pop



    def epoch(self):
        logger = logging.getLogger(__name__)
        epoch_cost = max([island.epoch(self.epoch_length) for island in self.islands])

        for i in range(len(self.islands)):
            island = self.islands[i]

            for n in self.topology[i]:
                self.islands[n].immigrate(island.emigrate())

        for island in self.islands:
            island.assimilate()

        return epoch_cost




    def create_islands(self, init_population):
        logger = logging.getLogger(__name__)
        subpop_size = int(len(init_population) / self.islands_number)

        subpopulations = [init_population[i*subpop_size:(i+1)*subpop_size] for i in range(self.islands_number)]

        for i in range(len(init_population) % self.islands_number):
            subpopulations[i].append(init_population[self.islands_number*subpop_size + i])

        logger.debug(subpopulations)

        return [IMGA.Island(self, subpop) for subpop in subpopulations]
    #- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    class Island:

        def __init__(self,
                     outer,
                     population):
            self.outer = outer
            self.population = population

            self.driver = outer.driver(population=population,
                                       dims=outer.dims,
                                       fitnesses=outer.fitnesses,
                                       mutation_variance=outer.mutation_variance,
                                       crossover_variance=outer.crossover_variance)
            if isinstance(self.driver, DriverGen):
                self.driver_gen = self.driver.population_generator()
                self.last_proxy = None
            self.visa_office = []
            self.all_refugees = []

        def epoch(self, epoch_length):
            if isinstance(self.driver, DriverGen):
                cost = 0
                for _ in range(epoch_length):
                    self.last_proxy = self.driver_gen.send(self.last_proxy)
                    cost += self.last_proxy.cost
                return cost
            else:
                return self.driver.steps(range(epoch_length))

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

                weights = [1/(i+1) for i in range(len(pareto_layers))]

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
                raise ValueError('Number of immigrants and emigrants should be equal: {} != {}'.format(len(self.visa_office), len(self.all_refugees)))

            if isinstance(self.driver, DriverGen):
                self.last_proxy.assimilate_immigrants(self.visa_office)
            else:
                current_population = self.driver.population
                current_population.extend(self.visa_office)
                self.driver.population = current_population

            logger.debug('after immigrate: ' + str(len(self.driver.population)))

            self.all_refugees.clear()
            self.visa_office.clear()

