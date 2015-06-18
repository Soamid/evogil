import random

from algorithms.IMGA.topology import TorusTopology, Topology
from algorithms.base.driverlegacy import DriverLegacy
from evotools import ea_utils
from evotools.log_helper import get_logger
from evotools.random_tools import weighted_choice

logger = get_logger(__name__)

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
        for _ in _iterator:
            logger.debug(self.epoch_no)
            self.epoch_no +=1
            cost = self.epoch()
            self.finish()
            self.cost += cost
            if budget is not None and self.cost > self.budget:
                break
        return self.cost

    def finish(self):
        global_pop = []
        for pop in [island.driver.finish() for island in self.islands]:
            global_pop.extend(pop)

        return global_pop



    def epoch(self):
        epoch_cost = max([island.driver.steps(range(self.epoch_length)) for island in self.islands])


        for i in range(len(self.islands)):
            island = self.islands[i]

            logger.debug('pop size: ' + str(len(island.driver.population)))
            for n in self.topology[i]:
                self.islands[n].immigrate(island.emigrate())

        for island in self.islands:
            island.assimilate()

        return epoch_cost




    def create_islands(self, init_population):
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
            self.visa_office = []
            self.refugees = []

        def emigrate(self):

            def fitfun_res(ind):
                return [f(ind) for f in self.outer.fitnesses]

            current_population = self.driver.population

            for _ in range(self.outer.migrants_number):
                pareto_layers = [l for l in ea_utils.paretofront_layers(current_population, fitfun_res=fitfun_res)]

                weights = [1/(i+1) for i in range(len(pareto_layers))]

                chosen_layer = weighted_choice(zip(pareto_layers, weights))

                refugee = random.choice(chosen_layer)
                self.refugees.append(refugee)
                current_population.remove(refugee)

                yield refugee

            self.driver.population = current_population

            logger.debug('after emigrate: ' + str(len(self.driver.population)))


        def immigrate(self, migrants):
            self.visa_office.extend(migrants)

        def assimilate(self):
            if len(self.visa_office) != len(self.refugees):
                raise ValueError('Number of immigrants and emigrants should be equal')

            current_population = self.driver.population

            #print(current_population)
            #print(self.refugees)

            current_population.extend(self.visa_office)

            self.driver.population = current_population

            logger.debug('after immigrate: ' + str(len(self.driver.population)))

            self.refugees.clear()
            self.visa_office.clear()

