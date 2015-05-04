"""
.. module:: spea2
    :platform: Unix, Windows
    :synopsis: Strength Pareto Evolutionary Algorithm
    :author: Michal Idzik <idzik@student.agh.edu.pl>
"""
import math
import random

from algorithms.utils.driver import Driver


class SPEA2(Driver):
    class Tournament:
        def __init__(self):
            self.tournament_size = 2

        def __call__(self, pool):
            sub_pool = random.sample(pool, self.tournament_size)
            return min(sub_pool, key=lambda x: x['fitness'])['value']

    def __init__(self, population, fitnesses, dims, mutation_variance, crossover_variance):
        super().__init__(population, dims, fitnesses, mutation_variance, crossover_variance)
        self.population = population
        self.__archive_size = len(population)
        self.__archive = []
        self.select = SPEA2.Tournament()

    @property
    def population(self):
        return [x['value'] for x in self.__population]

    @population.setter
    def population(self, pop):
        self.__population = [{'value': x} for x in pop]

    def finish(self):
        return [x['value'] for x in self.__archive]

    def steps(self):
        while True:
            self.calculate_fitnesses(self.__population, self.__archive)
            self.__archive = self.environmental_selection(self.__population, self.__archive)

            self.population = [self.mutate(self.crossover(self.select(self.__archive),
                                                          self.select(self.__archive)))
                               for _ in self.__population]
            cost = len(self.__population)

            yield cost, self.finish()

    def calculate_fitnesses(self, population, archive):
        self.calculate_objectives(population)
        union = archive + population
        self.calculate_dominated(union)

        for p in union:
            raw_fitness = self.calculate_raw_fitness(p, union)
            density = self.calculate_density(p, union)
            p['fitness'] = raw_fitness + density

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
        for p in pop:
            p['objectives'] = [o(p['value'])
                               for o in self.fitnesses]

    def calculate_dominated(self, pop):
        for p in pop:
            p['dominates'] = len([x
                                  for x in pop
                                  if id(p) != id(x) and self.dominates(p, x)])

    def dominates(self, p1, p2):
        at_least_one = False
        for i in range(0, len(p1['objectives'])):
            if p2['objectives'][i] < p1['objectives'][i]:
                return False
            elif p2['objectives'][i] > p1['objectives'][i]:
                at_least_one = True

        return at_least_one

    def euclidean_distance(self, c1, c2):
        dist_sum = 0.0
        for i in range(0, len(c1)):
            dist_sum += (c1[i] - c2[i]) ** 2.0
        return math.sqrt(dist_sum)

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

    def get_domination_index(self, sorted_pop):
        for i in range(0, len(sorted_pop)):
            if sorted_pop[i]['fitness'] > 1:
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
