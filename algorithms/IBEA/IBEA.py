import itertools
import math
import random
import sys

from algorithms.base.driver import Driver
from algorithms.base.drivertools import rank, mutate, crossover


class IBEA(Driver):
    def __init__(
        self,
        population,
        dims,
        fitnesses,
        kappa,
        mating_population_size,
        mutation_eta,
        crossover_eta,
        mutation_rate,
        crossover_rate,
        trim_function=lambda x: x,
        fitness_archive=None,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)

        self.individuals = []
        self.population_size = 0
        self.mating_size = 0

        self.dims = dims
        self.mutation_eta = mutation_eta
        self.mutation_rate = mutation_rate
        self.crossover_eta = crossover_eta
        self.crossover_rate = crossover_rate

        self.cost = 0
        self.objectives = fitnesses
        self.indicator = self.EPlusIndicator(self)
        self.generation_counter = 0
        self.k = kappa
        self.mating_size_c = mating_population_size
        self.trim_function = trim_function
        self.population = [self.trim_function(x) for x in population]

        self._scale_objectives()

        self.fitness_archive = fitness_archive

    def finalized_population(self):
        return self.finish()

    def get_indivs_inorder(self):
        return rank(self.population, self.calculate_objectives)

    def finish(self):
        self._scale_objectives()
        self._calculate_fitness()
        self._environmental_selection()
        return [x.v for x in self.individuals]

    def step(self):
        self._calculate_fitness()
        self._environmental_selection()
        self._mating_selection(0.9)
        self._crossover()
        self._mutation()  # (0.05)
        for ind in self.mating_individuals:
            ind.v = self.trim_function(ind.v)
        self.individuals += self.mating_individuals
        self._scale_objectives()
        self.generation_counter += 1

    def _scale_objectives(self):
        min_max = lambda x: (min(x), max(x))
        for ind in self.individuals:
            if not ind.known_objectives or not (
                (self.fitness_archive is not None) and (ind.v in self.fitness_archive)
            ):
                self.cost += 1
            ind.known_objectives = True
        measured = [
            (objective, min_max([objective(ind.v) for ind in self.individuals]))
            for objective in self.objectives
        ]
        self.scaled_objectives = [
            self._scale(objective, min_o, max_o)
            for objective, (min_o, max_o) in measured
        ]

    @staticmethod
    def _scale(fun, min_o, max_o):
        def scaled(x):
            return (fun(x) - min_o) / (max_o - min_o + sys.float_info.epsilon)

        return scaled

    def _calculate_fitness(self):
        self.indicators = {
            (x1, x2): self.indicator(x1.v, x2.v)
            for x1, x2 in itertools.product(self.individuals, self.individuals)
        }
        self.c = max([abs(x) for x in self.indicators.values()])
        self.fitness = {
            x1: sum(
                [
                    (-1)
                    * math.exp(
                        (-1)
                        * (
                            self.indicators[(x2, x1)]
                            / abs(self.c * self.k + sys.float_info.epsilon)
                        )
                    )
                    for x2 in self.individuals
                    if x2 != x1
                ]
            )
            for x1 in self.individuals
        }

    def _environmental_selection(self):
        while len(self.individuals) > self.population_size:
            self.individuals = sorted(
                self.individuals, key=lambda y: self.fitness[y], reverse=True
            )
            removed = self.individuals.pop()
            for x in self.individuals:
                self.fitness[x] += math.exp(
                    (-1)
                    * (
                        self.indicators[(removed, x)]
                        / abs(self.c * self.k + sys.float_info.epsilon)
                    )
                )

    def _mating_selection(self, p):
        coin = lambda: random.random() < p
        better = (
            lambda x1, x2: self.fitness[x1] < self.fitness[x2] and x1 or x2
            if coin()
            else self.fitness[x1] > self.fitness[x2] and x1 or x2
        )
        self.mating_individuals = [
            better(random.choice(self.individuals), random.choice(self.individuals))
            for _ in range(2 * self.mating_size)
        ]

    def _crossover(self):
        self.mating_individuals = [
            crossover(
                self.mating_individuals[i].v,
                self.mating_individuals[self.mating_size + i].v,
                self.dims,
                self.crossover_rate,
                self.crossover_eta,
            )
            for i in range(self.mating_size)
        ]

    def _mutation(self):
        self.mating_individuals = [
            self.Individual(mutate(x, self.dims, self.mutation_rate, self.mutation_eta))
            for x in self.mating_individuals
        ]
        for ind in self.mating_individuals:
            ind.known_objectives = False

    @property
    def population(self):
        return [x.v for x in self.individuals]

    @population.setter
    def population(self, pop):
        self.individuals = [self.Individual(x) for x in pop]
        self.population_size = len(self.individuals)
        self.mating_size = int(self.mating_size_c * self.population_size)

    def calculate_objectives(self, ind):
        if (self.fitness_archive is not None) and (ind.v in self.fitness_archive):
            return self.fitness_archive[ind.v]
        if not ind.known_objectives:
            self.cost += 1
        return [objective(ind.v) for objective in self.objectives]

    class EPlusIndicator:
        def __init__(self, population):
            self.population = population

        def __call__(self, x1, x2):
            return max(
                [
                    objective(x1) - objective(x2)
                    for objective in self.population.scaled_objectives
                ]
            )

    class Individual:
        def __init__(self, vector):
            self.v = vector
            self.known_objectives = False


if __name__ == "__main__":
    pass
    # import pylab
    # # objectives = [lambda x : (x[0]+5)*(x[0]+5), lambda x : (x[1]-5)*(x[1]-5)]
    # objectives = [lambda x: -10 * math.exp(-0.2 * math.sqrt(x[0] * x[0] + x[1] * x[1])),
    # lambda x: math.pow(abs(x[0]), 0.8) + 5 * math.pow(math.sin(x[0]), 3) + math.pow(abs(x[1]),
    #                                                                                               0.8) + 5 * math.pow(
    #                   math.sin(x[1]), 3)
    # ]
    # dimensions = [(-10, 10),
    #               (-10, 10)
    # ]
    # individuals = [[random.uniform(-10, 10), random.uniform(-10, 10)]
    #                for _
    #                in range(150)
    # ]
    # kappa = 0.05
    # mating_size = 50
    # raise CodeSmell("IBEA does not take those arguments…")
    # # noinspection PyArgumentList
    # population = IBEA(objectives, dimensions, individuals, kappa, mating_size)
    # for i in range(100):
    #     population.step()
    #     print(i)
    # effect = population.finish()
    # X = [population.objectives[0](x) for x in effect]
    # Y = [population.objectives[1](x) for x in effect]
    # pylab.scatter(X, Y)
    # # pylab.xlim(-10.,250.)
    # # pylab.ylim(-10.,250.)
    # pylab.xlim(-15., 5.)
    # pylab.ylim(-15., 25.)
    # pylab.show()
