import math
import random

import numpy as np
from sklearn import lda

from algorithms.base.drivergen import DriverGen
from algorithms.base import drivertools

np.seterr(all='raise')


class RHGS(DriverGen):
    def __init__(self,
                 population,
                 dims,
                 fitnesses,
                 driver,
                 mutation_etas,
                 crossover_etas,
                 mutation_rates,
                 crossover_rates,
                 delegates_no,
                 metaepoch_len=5,
                 max_level=2,
                 max_sprouts_no=20,
                 sproutiveness=1,
                 comparison_multiplier=2.0,
                 population_sizes=(64, 16, 4)):
        super().__init__()

        self.driver = driver

        self.dims = dims
        self.fitnesses = fitnesses

        self.metaepoch_len = metaepoch_len
        self.max_level = max_level
        self.max_sprouts_no = max_sprouts_no
        self.comparison_multiplier = comparison_multiplier
        self.sproutiveness = sproutiveness

        self.mutation_etas = mutation_etas
        self.mutation_rates = mutation_rates
        self.crossover_etas = crossover_etas
        self.crossover_rates = crossover_rates
        self.population_sizes = population_sizes
        self.delegates_no = delegates_no

        self.root = RHGS.Node(self, 0, random.sample(population, self.population_sizes[0]))
        self.nodes = [self.root]

        self.cost = 0

    class RHGSProxy(DriverGen.Proxy):
        def __init__(self, cost, driver):
            super().__init__(cost)
            self.cost = cost
            self.driver = driver

        def finalized_population(self):
            return self.merge_node_populations()

        def current_population(self):
            return self.merge_node_populations()

        def deport_emigrants(self, immigrants):
            raise Exception("RHGS does not support migrations")

        def assimilate_immigrants(self, emigrants):
            raise Exception("RHGS does not support migrations")

        def nominate_delegates(self, delegates_no):
            raise Exception("RHGS does not support sprouting")

        def merge_node_populations(self):
            merged_population = []
            for node in self.driver.nodes:
                merged_population.extend(node.population)
            return merged_population

    def population_generator(self):
        while True:
            self.next_step()
            yield RHGS.RHGSProxy(self.cost, self)
            self.cost = 0
        return self.cost

    def next_step(self):
        self.run_metaepoch()
        self.trim_sprouts()
        self.release_new_sprouts()

    def run_metaepoch(self):
        for node in self.nodes:
            node.run_metaepoch()

    def trim_sprouts(self):
        self.root.trim_sprouts()

    def release_new_sprouts(self):
        self.root.release_new_sprouts()

    class Node():
        def __init__(self,
                     owner,
                     level,
                     population):
            self.alive = True
            self.owner = owner
            self.level = level
            self.driver = owner.driver(population=population,
                                       dims=owner.dims,
                                       fitnesses=owner.fitnesses,
                                       mutation_eta=owner.mutation_etas[self.level],
                                       mutation_rate=owner.mutation_rates[self.level],
                                       crossover_eta=owner.crossover_etas[self.level],
                                       crossover_rate=owner.crossover_rates[self.level])
            self.population = []
            self.sprouts = []
            self.delegates = []

            self.old_average_fitnesses = [float('inf') for _ in self.owner.fitnesses]
            self.average_fitnesses = [float('inf') for _ in self.owner.fitnesses]

        def run_metaepoch(self):
            if self.alive:
                iterations = 0
                final_proxy = None
                for proxy in self.driver.population_generator():
                    self.owner.cost += proxy.cost
                    final_proxy = proxy
                    iterations += 1
                    if not iterations < self.owner.metaepoch_len:
                        break
                self.population = final_proxy.finalized_population()
                self.delegates = final_proxy.nominate_delegates(self.owner.delegates_no[self.level])
                random.shuffle(self.delegates)
                self.update_average_fitnesses()

        def trim_sprouts(self):
            for sprout in self.sprouts:
                sprout.trim_sprouts()
            self.trim_not_progressing()
            self.trim_redundant()

        def trim_not_progressing(self):
            for sprout in [x for x in self.sprouts if x.alive]:
                if not any(new > old for new, old in zip(self.average_fitnesses, self.old_average_fitnesses)):
                    sprout.alive = False

        def update_average_fitnesses(self):
            self.old_average_fitnesses = self.average_fitnesses
            fitness_values = [[f(p) for f in self.owner.fitnesses] for p in self.population]
            self.average_fitnesses = np.mean(fitness_values, axis=0)

        def trim_redundant(self):
            for sprout in [x for x in self.sprouts if x.alive]:
                for another_sprout in self.sprouts:
                    if not sprout.alive:
                        break
                    if redundant(another_sprout.population, sprout.population, self.owner.comparison_multiplier):
                        sprout.alive = False

        def release_new_sprouts(self):
            for sprout in self.sprouts:
                sprout.release_new_sprouts()
            # TODO: limit na wszystkich sproutach, czy tylko na tych żywych?
            if self.alive and self.level < self.owner.max_level and len(self.sprouts) < self.owner.max_sprouts_no:
                released_sprouts = 0
                for delegate in self.delegates:
                    if released_sprouts >= self.owner.sproutiveness or len(self.sprouts) >= self.owner.max_sprouts_no:
                        break
                    candidate_population = population_from_delegate(delegate,
                                                                    self.owner.population_sizes[self.level + 1],
                                                                    self.owner.dims,
                                                                    self.owner.mutation_rates[self.level + 1],
                                                                    self.owner.mutation_etas[self.level + 1])
                    if not any([redundant(candidate_population, sprout.population, self.owner.comparison_multiplier)
                                for sprout in self.sprouts]):
                        new_sprout = RHGS.Node(self.owner, self.level + 1, candidate_population)
                        self.sprouts.append(new_sprout)
                        self.owner.nodes.append(new_sprout)
                        released_sprouts += 1


def population_from_delegate(delegate, size, dims, rate, eta):
    population = [[x for x in delegate]]
    for _ in range(size - 1):
        population.append(drivertools.mutate(delegate, dims, rate, eta))
    return population


def redundant(pop_a, pop_b, variances_multiplier=2.0):
    if pop_a is pop_b:
        return False

    combined = [x for x in pop_a]
    combined_class = [0 for _ in pop_a]
    for x in pop_b:
        combined.append(x)
        combined_class.append(1)

    lda_instance = lda.LDA(n_components=1)
    lda_projection = None
    while lda_projection is None:
        try:
            lda_projection = [x[0] for x in lda_instance.fit_transform(combined, combined_class)]
        except ValueError:
            print("intelowy error")

    projection_a = [x for i, x in enumerate(lda_projection) if combined_class[i] == 0]
    projection_b = [x for i, x in enumerate(lda_projection) if combined_class[i] == 1]

    mean_a = np.mean(projection_a)
    mean_b = np.mean(projection_b)

    std_a = np.std(projection_a)
    std_b = np.std(projection_b)

    return (variances_multiplier * (std_a + std_b)) > math.fabs(mean_a - mean_b)