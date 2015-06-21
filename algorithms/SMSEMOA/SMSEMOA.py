import logging
import random
import collections

from algorithms.base.driverlegacy import DriverLegacy
from algorithms.base.hv import HyperVolume
from evotools import ea_utils

class SMSEMOA(DriverLegacy):
    def __init__(self, population, fitnesses, dims, mutation_variance, crossover_variance, reference_point, epoch_length_multiplier=0.5):
        super().__init__(population, dims, fitnesses, mutation_variance, crossover_variance)
        self.population = population
        self.epoch_length = int(len(self.__population) * epoch_length_multiplier)
        self.reference_point = reference_point


    @property
    def population(self):
        return [x.value for x in self.__population]

    @population.setter
    def population(self, pop):
        self.__population = [Individual(x) for x in pop]

    def finish(self):
        return self.population

    def steps(self, condI, budget=None):
        logger = logging.getLogger(__name__)
        cost = self.calculate_objectives(self.__population)

        i = 1

        for _ in condI:
            for _ in range(self.epoch_length):
                new_indiv = self.generate(self.__population)
                cost += self.calculate_objectives([new_indiv])
                self.__population = self.reduce_population(self.__population + [new_indiv])

                if budget is not None and cost > budget:
                    logger.debug(i)
                    return cost

                i+=1

        return cost


    def calculate_objectives(self, pop):
        for p in pop:
            p.objectives = [o(p.value)
                            for o in self.fitnesses]
        return len(pop)

    def generate(self, pop):
        selected_parents = [x.value for x in random.sample(pop, 2)]
        child = self.crossover(*selected_parents)

        return Individual(self.mutate(child))


    def reduce_population(self, pop):
        sorted_pop = self.nd_sort(pop)
        worst_front = max(sorted_pop.items(), key=lambda x: x[0])[1]

        hv_contribution = self.calculate_hypervolume_contribution(worst_front)
        min_contributor = min(hv_contribution, key=lambda x: x[1])

        pop.remove(min_contributor[0])
        return pop

    def calculate_hypervolume_contribution(self, pop):
        hv = HyperVolume(self.reference_point)
        results = [x.objectives for x in pop]

        hv_global = hv.compute(results)

        return [(pop[i], hv_global - hv.compute(results[:i] + results[i + 1:])) for i in range(len(results))]

    def nd_sort(self, pop):
        dominated_by = collections.defaultdict(set)
        how_many_dominates = collections.defaultdict(int)
        front = collections.defaultdict(list)

        for x in pop:
            for y in pop:
                if ea_utils.dominates(x.objectives, y.objectives):
                    dominated_by[x].add(y)
                elif ea_utils.dominates(y.objectives, x.objectives):
                    how_many_dominates[x] += 1
            if how_many_dominates[x] is 0:
                front[1].append(x)
        front_no = 1
        while True:
            if len(front[front_no]) is 0:
                break
            for x in front[front_no]:
                for y in dominated_by[x]:
                    how_many_dominates[y] -= 1
                    if how_many_dominates[y] is 0:
                        front[front_no + 1].append(y)
            front_no += 1
        del front[front_no]
        return front


class Individual:
    def __init__(self, value):
        self.value = value
        self.objectives = []