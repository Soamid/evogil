import logging
import random

import collections

from algorithms.base.driver import Driver
from algorithms.base.drivertools import crossover, mutate
from algorithms.base.hv import HyperVolume
from evotools import ea_utils


class SMSEMOA(Driver):
    def __init__(
        self,
        population,
        fitnesses,
        dims,
        mutation_eta,
        mutation_rate,
        crossover_eta,
        crossover_rate,
        reference_point,
        epoch_length_multiplier=0.5,
        trim_function=lambda x: x,
        fitness_archive=None,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.fitnesses = fitnesses
        self.dims = dims
        self.mutation_eta = mutation_eta
        self.mutation_rate = mutation_rate
        self.crossover_eta = crossover_eta
        self.crossover_rate = crossover_rate

        self.trim_function = trim_function
        self.population = [self.trim_function(x) for x in population]
        self.epoch_length = int(len(self.individuals) * epoch_length_multiplier)
        self.reference_point = reference_point

        self.fitness_archive = fitness_archive

        self.logger = logging.getLogger(__name__)
        self.cost = self.calculate_objectives(self.individuals)

    @property
    def population(self):
        return [x.value for x in self.individuals]

    @population.setter
    def population(self, pop):
        self.individuals = [Individual(x) for x in pop]

    def finalized_population(self):
        return [x.value for x in self.individuals]

    def step(self):
        for _ in range(self.epoch_length):
            new_indiv = self.generate(self.individuals)
            self.cost += self.calculate_objectives([new_indiv])
            self.individuals = self.reduce_population(self.individuals + [new_indiv])

    def calculate_objectives(self, pop):
        objectives_cost = 0
        for p in pop:
            if (self.fitness_archive is not None) and (p.value in self.fitness_archive):
                p.objectives = self.fitness_archive[p.value]
                objectives_cost = 0
            else:
                p.objectives = [o(p.value) for o in self.fitnesses]
                objectives_cost = len(self.population)
        return objectives_cost

    def generate(self, pop):
        selected_parents = [x.value for x in random.sample(pop, 2)]
        child = crossover(
            selected_parents[0],
            selected_parents[1],
            self.dims,
            self.crossover_rate,
            self.crossover_eta,
        )

        return Individual(
            self.trim_function(
                mutate(child, self.dims, self.mutation_rate, self.mutation_eta)
            )
        )

    def reduce_population(self, pop):
        sorted_pop = nd_sort(pop)
        worst_front = max(sorted_pop.items(), key=lambda x: x[0])[1]

        hv_contribution = self.calculate_hypervolume_contribution(worst_front)
        min_contributor = min(hv_contribution, key=lambda x: x[1])

        pop.remove(min_contributor[0])
        return pop

    def calculate_hypervolume_contribution(self, pop):
        hv = HyperVolume(self.reference_point)
        results = [x.objectives for x in pop]

        hv_global = hv.compute(results)

        return [
            (pop[i], hv_global - hv.compute(results[:i] + results[i + 1 :]))
            for i in range(len(results))
        ]


def nd_sort(pop):
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
