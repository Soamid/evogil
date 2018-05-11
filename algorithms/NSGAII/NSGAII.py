from algorithms.base.drivergen import ImgaProxy, Driver
from algorithms.base.drivertools import mutate, crossover

__author__ = 'Prpht'

import collections
import random
import sys


def dominates_weak(x, y):
    return all([a <= b for a, b in zip(x.objectives.values(), y.objectives.values())])


def dominates(x, y):
    a = dominates_weak(x, y) and not dominates_weak(y, x)
    # looks like debug?
    # x.objectives = {objective: objective(x.v) for objective in self.objectives}
    # y.objectives = {objective: objective(y.v) for objective in self.objectives}
    # b = dominates_weak(x, y) and not dominates_weak(y, x)
    # if a is b:
    # return a
    # elif a is not b:
    # print("Something terrible had happend while calculating domination, indeed...")
    return a


class NSGAII(Driver):
    class NSGAIIImgaProxy(ImgaProxy):
        def __init__(self, driver, cost, individuals):
            super().__init__(driver, cost)
            self.individuals = individuals

        def finalized_population(self):
            return self.driver.finish()

        def current_population(self):
            return [x.v for x in self.individuals]

        def deport_emigrants(self, immigrants, remove=True):
            immigrants_cp = list(immigrants)
            to_remove = []

            for p in self.individuals:
                if p.v in immigrants_cp:
                    to_remove.append(p)
                    immigrants_cp.remove(p.v)

            if remove:
                for p in to_remove:
                    self.individuals.remove(p)
                return to_remove
            else:
                return [NSGAII.Individual([vec for vec in x.v]) for x in to_remove]

        def assimilate_immigrants(self, emigrants):
            self.individuals.extend(emigrants)

        def nominate_delegates(self):
            self.driver.finish()
            return [x.v for x in self.driver.front[1]]

    def __init__(self,
                 population,
                 dims,
                 fitnesses,
                 mating_population_size,
                 mutation_eta,
                 crossover_eta,
                 mutation_rate,
                 crossover_rate,
                 trim_function=lambda x: x,
                 fitness_archive=None):
        super().__init__()

        self.dims = dims

        self.mutation_eta = mutation_eta
        self.mutation_rate = mutation_rate
        self.crossover_eta = crossover_eta
        self.crossover_rate = crossover_rate

        self.cost = 0
        self.objectives = fitnesses
        self.mating_size_c = mating_population_size
        self.generation_counter = 0

        self.trim_function = trim_function
        self.fitness_archive = fitness_archive

        self.population_size = 0
        self.individuals = []
        self.mating_size = 0
        self.population = [self.trim_function(x) for x in population]

        self._calculate_objectives()

    @property
    def population(self):
        return [x.v for x in self.individuals]

    @population.setter
    def population(self, pop):
        self.individuals = [self.Individual(x) for x in pop]
        self.population_size = len(self.individuals)
        self.mating_size = int(self.mating_size_c * self.population_size)

    def step(self):
        self._next_step()
        return NSGAII.NSGAIIImgaProxy(self, self.cost, self.individuals)

    def finish(self):
        self._calculate_objectives()
        self._nd_sort()
        self._crowding()
        self._environmental_selection()
        return [x.v for x in self.individuals]

    def _next_step(self):
        self._nd_sort()
        self._crowding()
        self._environmental_selection()
        self._mating_selection(0.9)
        self._crossover()
        self._mutation()
        for ind in self.mating_individuals:
            ind.v = self.trim_function(ind.v)
        self.individuals += self.mating_individuals
        self._calculate_objectives()
        self.generation_counter += 1

    def _calculate_objectives(self):
        for ind in self.individuals:
            if ind.objectives is None:
                if (self.fitness_archive is not None) and (ind.v in self.fitness_archive):
                    fitnesses = self.fitness_archive[ind.v]
                else:
                    self.cost += 1
                    fitnesses = [objective(ind.v) for objective in self.objectives]
                    if self.fitness_archive is not None:
                        self.fitness_archive[ind.v] = fitnesses
                ind.objectives = {objective: fitness for objective, fitness in zip(self.objectives, fitnesses)}

    def _nd_sort(self):
        self.dominated_by = collections.defaultdict(set)
        self.how_many_dominates = collections.defaultdict(int)
        self.nsga_rank = collections.defaultdict(int)
        self.front = collections.defaultdict(list)
        for x in self.individuals:
            for y in self.individuals:
                if dominates(x, y):
                    self.dominated_by[x].add(y)
                elif dominates(y, x):
                    self.how_many_dominates[x] += 1
            if self.how_many_dominates[x] is 0:
                self.nsga_rank[x] = 1
                self.front[1].append(x)
        front_no = 1
        while True:
            if len(self.front[front_no]) is 0:
                break
            for x in self.front[front_no]:
                for y in self.dominated_by[x]:
                    self.how_many_dominates[y] -= 1
                    if self.how_many_dominates[y] is 0:
                        self.nsga_rank[y] = front_no + 1
                        self.front[front_no + 1].append(y)
            front_no += 1

    def _crowding(self):
        self.dist = collections.defaultdict(float)
        for front_no, inds in self.front.items():
            if len(inds) == 0:
                break
            elif len(inds) == 1:
                self.dist[inds[0]] = 0
            else:
                for objective in self.objectives:
                    inds.sort(key=lambda x: x.objectives[objective])
                    # self.dist[inds[0]] = self.dist[inds[-1]] = float('inf')
                    max_r = inds[-1].objectives[objective]
                    min_r = inds[0].objectives[objective]
                    self.dist[inds[0]] = float('inf')
                    self.dist[inds[-1]] += 2 * (inds[-1].objectives[objective] - inds[-2].objectives[objective]) / (
                            max_r - min_r + sys.float_info.epsilon)
                    for k in range(1, len(inds) - 1):
                        self.dist[inds[k]] += (inds[k + 1].objectives[objective] - inds[k - 1].objectives[
                            objective]) / (max_r - min_r + sys.float_info.epsilon)

    def _environmental_selection(self):
        fitness = lambda ind: (self.nsga_rank[ind], 1 / (self.dist[ind] + sys.float_info.epsilon))
        self.fitness = {ind: fitness(ind) for ind in self.individuals}
        self.individuals = sorted(self.individuals, key=lambda ind: self.fitness[ind])[:self.population_size]

    def _mating_selection(self, p):
        coin = lambda: random.random() < p
        better = lambda x1, x2: self.fitness[x1] < self.fitness[x2] and x1 or x2 if coin() \
            else self.fitness[x1] > self.fitness[x2] and x1 or x2
        self.mating_individuals = [better(random.choice(self.individuals), random.choice(self.individuals)) for _ in
                                   range(2 * self.mating_size)]

    def _crossover(self):
        self.mating_individuals = [
            crossover(self.mating_individuals[i].v, self.mating_individuals[self.mating_size + i].v, self.dims,
                      self.crossover_rate, self.crossover_eta) for i in
            range(self.mating_size)]

    def _mutation(self):
        self.mating_individuals = [
            self.Individual(mutate(x, self.dims, self.mutation_rate, self.mutation_eta)) for x in
            self.mating_individuals]

    class Individual:
        def __init__(self, vector):
            self.v = vector
            self.objectives = None


if __name__ == "__main__":
    pass
    # import pylab
    # # objectives = [lambda x : (x[0]+5)*(x[0]+5), lambda x : (x[1]-5)*(x[1]-5)]
    # objectives = [lambda x: -10 * math.exp(-0.2 * math.sqrt(x[0] * x[0] + x[1] * x[1])),
    # lambda x: math.pow(abs(x[0]), 0.8) + 5 * math.pow(math.sin(x[0]), 3) + math.pow(abs(x[1]),
    # 0.8) + 5 * math.pow(
    # math.sin(x[1]), 3)]
    # dimensions = [(-10, 10), (-10, 10)]
    # individuals = [[random.uniform(-10, 10), random.uniform(-10, 10)] for _ in range(50)]
    # mating_size = 20
    # population = NSGA2(objectives, dimensions, individuals, mating_size)
    # for i in range(100):
    # population.step()
    # print(i)
    # effect = population.finish()
    # X = [population.objectives[0](x) for x in effect]
    # Y = [population.objectives[1](x) for x in effect]
    # pylab.scatter(X, Y)
    # # pylab.xlim(-10.,250.)
    # # pylab.ylim(-10.,250.)
    # pylab.xlim(-15., 5.)
    # pylab.ylim(-15., 25.)
    # pylab.show()
