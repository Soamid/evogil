"""
.. module:: spea2
    :platform: Unix, Windows
    :synopsis: Strength Pareto Evolutionary Algorithm
    :author: Michal Idzik <idzik@student.agh.edu.pl>
"""
import math
import random

from algorithms.base.driver import Driver
from algorithms.base.drivertools import crossover, mutate
from evotools import ea_utils
from metrics.metrics_utils import euclid_distance


class SPEA2(Driver):
    class Tournament:
        def __init__(self):
            self.tournament_size = 2

        def __call__(self, pool):
            sub_pool = random.sample(pool, self.tournament_size)
            return min(sub_pool, key=lambda x: x['fitness'])['value']

    def __init__(self,
                 population,
                 fitnesses,
                 dims,
                 mutation_eta,
                 mutation_rate,
                 crossover_eta,
                 crossover_rate,
                 trim_function=lambda x: x,
                 fitness_archive=None,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fitnesses = fitnesses
        self.dims = dims
        self.mutation_eta = mutation_eta
        self.mutation_rate = mutation_rate
        self.crossover_eta = crossover_eta
        self.crossover_rate = crossover_rate
        self.trim_function = trim_function
        self.population = [self.trim_function(x) for x in population]

        self.__archive_size = len(population)
        self.archive = []
        self.select = SPEA2.Tournament()

        self.fitness_archive = fitness_archive

    @property
    def population(self):
        return [x['value'] for x in self.individuals]

    @population.setter
    def population(self, pop):
        self.individuals = [{'value': x} for x in pop]

    def finalized_population(self):
        return [x['value'] for x in self.archive]

    def finish(self):
        return [x['value'] for x in self.archive]

    def step(self):
        self.cost += self.calculate_fitnesses(self.individuals, self.archive)
        self.archive = self.environmental_selection(self.individuals, self.archive)

        self.population = [self.trim_function(mutate(
            crossover(self.select(self.archive),
                      self.select(self.archive),
                      self.dims,
                      self.crossover_rate,
                      self.crossover_eta),
            self.dims,
            self.mutation_rate,
            self.mutation_eta))
            for _ in self.individuals]

    def calculate_fitnesses(self, population, archive):
        objectives_cost = self.calculate_objectives(population)
        union = archive + population
        self.calculate_dominated(union)

        for p in union:
            raw_fitness = self.calculate_raw_fitness(p, union)
            density = self.calculate_density(p, union)
            p['fitness'] = raw_fitness + density
        return objectives_cost

    def calculate_raw_fitness(self, p1, pop):
        return 0. + sum(y['dominates']
                        for y in pop
                        if self.dominates(y, p1))

    def calculate_density(self, p1, pop):
        distances = sorted([self.euclidean_distance(p1['objectives'], p2['objectives'])
                            for p2 in pop])
        k = int(math.sqrt(len(pop)))
        return 1.0 / (distances[k] + 2.0)

    def calculate_objectives(self, pop):
        objectives_cost = 0
        for p in pop:
            if (self.fitness_archive is not None) and (p['value'] in self.fitness_archive):
                p['objectives'] = self.fitness_archive[p['value']]
                objectives_cost = 0
            else:
                p['objectives'] = [o(p['value'])
                                   for o in self.fitnesses]
                objectives_cost = len(self.population)
        return objectives_cost

    def calculate_dominated(self, pop):
        for p in pop:
            p['dominates'] = len([x
                                  for x in pop
                                  if id(p) != id(x) and self.dominates(p, x)])

    @staticmethod
    def dominates(p1, p2):
        return ea_utils.dominates(p1['objectives'], p2['objectives'])

    @staticmethod
    def euclidean_distance(c1, c2):
        return euclid_distance(c1, c2)

    def environmental_selection(self, pop, archive):
        union = archive + pop
        sorted_union = sorted(union, key=lambda x: x['fitness'])
        index = self.get_domination_index(sorted_union)
        environment = sorted_union[:index]

        if len(environment) < self.__archive_size:
            diff_size = self.__archive_size - len(environment)
            environment += sorted_union[index:index + diff_size]

        elif len(environment) > self.__archive_size:
            while len(environment) > self.__archive_size:
                to_truncate = self.choose_to_truncate(environment)
                environment.remove(to_truncate)

        return environment

    @staticmethod
    def get_domination_index(sorted_pop):
        for i, p in enumerate(sorted_pop):
            if p['fitness'] > 1:
                return i

        return len(sorted_pop)

    def choose_to_truncate(self, pop):
        distances = []
        for p in pop:
            distances.append((p,
                              sorted([(p2, self.euclidean_distance(p['objectives'], p2['objectives'])) for p2 in pop],
                                     key=lambda x: x[1])))

        return self.get_min(distances, 0)[0]

    def get_min(self, distances, level):
        if level >= len(distances):
            return distances[0]

        sorted_distances = sorted(distances, key=lambda dist: dist[1][level][1])
        result = [sorted_distances[0]]
        for d in sorted_distances[1:]:
            if d[1][level][1] == result[0][1][level][1]:
                result.append(d)
            else:
                break

        if len(result) > 1:
            return self.get_min(result, level + 1)

        return result[0]
