import random

import matplotlib.pyplot as plt
import numpy as np

from algorithms.base.drivergen import DriverGen
from algorithms.base import drivertools
from algorithms.base.hv import HyperVolume

# np.seterr(all='raise')
EPSILON = np.finfo(float).eps


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
                 reference_point,
                 max_sprouts_trials,
                 metaepoch_len=5,
                 max_level=2,
                 max_sprouts_no=20,
                 sproutiveness=1,
                 comparison_multipliers=(1.0, 0.1, 0.01),
                 population_sizes=(64, 16, 4)):
        super().__init__()

        self.driver = driver

        self.dims = dims
        self.reference_point = reference_point
        self.fitnesses = fitnesses

        corner_a = np.array([x for x, _ in dims])
        corner_b = np.array([x for _, x in dims])
        corner_dist = np.linalg.norm(corner_a - corner_b)
        self.min_dists = [x*corner_dist for x in comparison_multipliers]

        self.metaepoch_len = metaepoch_len
        self.max_level = max_level
        self.max_sprouts_no = max_sprouts_no
        self.sproutiveness = sproutiveness
        self.max_sprouts_trials = max_sprouts_trials

        self.mutation_etas = mutation_etas
        self.mutation_rates = mutation_rates
        self.crossover_etas = crossover_etas
        self.crossover_rates = crossover_rates
        self.population_sizes = population_sizes

        self.root = RHGS.Node(self, 0, random.sample(population, self.population_sizes[0]))
        self.nodes = [self.root]
        self.level_nodes = {
            0: [self.root],
            1: [],
            2: [],
        }

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

        def nominate_delegates(self):
            raise Exception("RHGS does not support sprouting")

        def merge_node_populations(self):
            merged_population = []
            for node in self.driver.nodes:
                merged_population.extend(node.population)
            return merged_population

    def population_generator(self):
        # for _ in range(20):
        #     self.root.run_metaepoch()
        while True:
            self.next_step()
            yield RHGS.RHGSProxy(self.cost, self)
            self.cost = 0
        return self.cost

    def next_step(self):
        # print("nodes_no", len(self.nodes), "alive_no", len([x for x in self.nodes if x.alive]))
        print("nodes:", len(self.nodes), len([x for x in self.nodes if x.alive]),
              "   zer:", len(self.level_nodes[0]), len([x for x in self.level_nodes[0] if x.alive]), len([x for x in self.level_nodes[0] if x.ripe]),
              "   one:", len(self.level_nodes[1]), len([x for x in self.level_nodes[1] if x.alive]), len([x for x in self.level_nodes[1] if x.ripe]),
              "   two:", len(self.level_nodes[2]), len([x for x in self.level_nodes[2] if x.alive]), len([x for x in self.level_nodes[2] if x.ripe]))

        self.run_metaepoch()

        colors = ['r', 'g', 'b', 'c', 'm', 'y', 'k']

        # _plot_node(self.root, 'r', self.dims)
        # _plot_node(self.root, 'b', self.dims, delegates=True)
        # plt.show()

        # i = 0
        # for node in self.level_nodes[1]:
        #     _plot_node(node, colors[i], self.dims)
        #     i += 1
        #     i %= len(colors)
        # plt.show()

        self.trim_sprouts()

        # i = 0
        # for node in self.level_nodes[1]:
        #     _plot_node(node, colors[i], self.dims)
        #     i += 1
        #     i %= len(colors)
        # plt.show()

        self.release_new_sprouts()

    def run_metaepoch(self):
        for node in self.level_nodes[2]:
            node.run_metaepoch()
        for node in self.level_nodes[1]:
            node.run_metaepoch()
        for node in self.level_nodes[0]:
            node.run_metaepoch()

    def trim_sprouts(self):
        self.trim_all(self.level_nodes[2])
        self.trim_all(self.level_nodes[1])
        self.trim_all(self.level_nodes[0])

    def trim_all(self, nodes):
        self.trim_not_progressing(nodes)
        self.trim_redundant(nodes)

    def trim_not_progressing(self, nodes):
        for sprout in [x for x in nodes if x.alive]:
            if sprout.old_hypervolume is not None and ((sprout.hypervolume/(sprout.old_hypervolume + EPSILON)) - 1.0) < 0.001:
            # if not sprout.hypervolume > sprout.old_hypervolume:
            # if not any(new < old for new, old in zip(self.average_fitnesses, self.old_average_fitnesses)):
            #     # print(self.old_average_fitnesses)
            #     # print(self.average_fitnesses)
            #     print("!!! zabijam bo brak progressu") TODO print
                sprout.alive = False
                sprout.ripe = True
                sprout.sprouts_trials = 0
                sprout.center = np.mean(sprout.population, axis=0)
                if not (sprout.parent is None):
                    delegates = sprout.delegates
                    emmigrants = sprout.final_proxy.deport_emigrants(delegates)
                    sprout.parent.final_proxy.assimilate_immigrants(emmigrants)
                    sprout.parent.alive = True
                    sprout.parent.ripe = False
                    # print("ozywiony", sprout.parent.level)  TODO print

    def trim_redundant(self, nodes):
        alive = [x for x in nodes if x.alive]
        processed = []
        dead = [x for x in nodes if not x.alive]
        for sprout in alive:
            to_compare = [x for x in dead]
            to_compare.extend(processed)
            sprout.center = np.mean(sprout.population, axis=0)
            for another_sprout in to_compare:
                if not sprout.alive:
                    break
                if another_sprout.alive or ((not another_sprout.alive) and another_sprout.ripe):
                    if redundant([another_sprout.center], [sprout.center], self.min_dists[sprout.level]):
                            # print("!!! zabijam bo redundantny")  TODO print
                            # if sprout.level == 1:
                            #     _plot_node(sprout, 'r', self.dims)
                            #     _plot_node(another_sprout, 'b', self.dims)
                        sprout.alive = False
                        # else:
                            # if sprout.level == 1:
                            #     _plot_node(sprout, 'g', self.dims)
                            #     _plot_node(another_sprout, 'b', self.dims)
                    # plt.show()
            processed.append(sprout)

    def release_new_sprouts(self):
        self.root.release_new_sprouts()

    class Node():
        def __init__(self,
                     owner,
                     level,
                     population,
                     parent=None):
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

            self.relative_hypervolume = None
            self.old_hypervolume = None
            self.hypervolume = float('-inf')

            self.ripe = False
            self.parent = parent
            self.final_proxy = None
            self.sprout_trials = 0

        def run_metaepoch(self):
            if (self.sprout_trials == self.owner.max_sprouts_trials) and (not self.level == 2) and ((not self.alive) and self.ripe) and len([x for x in self.sprouts if x.alive]) == 0:
                self.alive = True
                self.ripe = False
            if self.alive:
                iterations = 0
                self.final_proxy = None
                for proxy in self.driver.population_generator():
                    self.owner.cost += proxy.cost
                    self.final_proxy = proxy
                    iterations += 1
                    if not iterations < self.owner.metaepoch_len:
                        break
                self.population = self.final_proxy.finalized_population()
                self.delegates = self.final_proxy.nominate_delegates()
                random.shuffle(self.delegates)
                # self.update_average_fitnesses()
                self.update_dominated_hypervolume()

        def update_average_fitnesses(self):
            self.old_average_fitnesses = self.average_fitnesses
            fitness_values = [[f(p) for f in self.owner.fitnesses] for p in self.population]
            self.average_fitnesses = np.mean(fitness_values, axis=0)

        def update_dominated_hypervolume(self):
            self.old_hypervolume = self.hypervolume
            fitness_values = [[f(p) for f in self.owner.fitnesses] for p in self.population]
            hv = HyperVolume(self.owner.reference_point)
            if self.relative_hypervolume is None:
                self.relative_hypervolume = hv.compute(fitness_values)
            self.hypervolume = hv.compute(fitness_values) - self.relative_hypervolume

            if self.level == 0:
                if self.old_hypervolume is not None:
                    print((self.hypervolume/(self.old_hypervolume + EPSILON)) - 1.0)
                # print(self.hypervolume)

        def release_new_sprouts(self):
            for sprout in self.sprouts:
                sprout.release_new_sprouts()
            # TODO: limit na wszystkich sproutach, czy tylko na tych żywych?
            if self.ripe and self.sprout_trials < self.owner.max_sprouts_trials and self.level < self.owner.max_level and len([x for x in self.sprouts if x.alive]) < self.owner.max_sprouts_no:
                released_sprouts = 0
                for delegate in self.delegates:
                    self.sprout_trials += 1
                    if released_sprouts >= self.owner.sproutiveness or len([x for x in self.sprouts if x.alive]) >= self.owner.max_sprouts_no:
                        # print("przeglem z iloscia zywych")
                        break

                    if not any([redundant([delegate], [sprout.center], self.owner.min_dists[self.level + 1])
                                for sprout in [x for x in self.owner.level_nodes[self.level+1]
                                               if len(x.population) > 0] if sprout.alive or ((not sprout.alive) and sprout.ripe)]):

                        candidate_population = population_from_delegate(delegate,
                                                self.owner.population_sizes[self.level + 1],
                                                self.owner.dims,
                                                self.owner.mutation_rates[self.level + 1],
                                                self.owner.mutation_etas[self.level + 1]/2.0)

                        new_sprout = RHGS.Node(self.owner, self.level + 1, candidate_population, self)
                        self.sprouts.append(new_sprout)
                        self.owner.nodes.append(new_sprout)
                        self.owner.level_nodes[self.level + 1].append(new_sprout)
                        released_sprouts += 1
                    else:
                        # print("### nie udalo sie sproutowac, bo redundantny")
                        pass


def population_from_delegate(delegate, size, dims, rate, eta):
    population = [[x for x in delegate]]
    for _ in range(size - 1):
        population.append(drivertools.mutate(delegate, dims, rate, eta))
    return population


def redundant(pop_a, pop_b, min_dist):
    mean_pop_a = np.mean(pop_a, axis=0)
    mean_pop_b = np.mean(pop_b, axis=0)

    dist = np.linalg.norm(mean_pop_a - mean_pop_b)
    return dist < min_dist


import matplotlib.pyplot as plt


def _plot_node(node, color, dims, delegates=False):
    if not delegates:
        pop = node.population
    else:
        pop = node.delegates

    if node.alive:
        marker = 'o'
    else:
        marker = '+'
    plt.scatter(
        [x[0] for x in pop],
        [x[1] for x in pop],
        color=color,
        marker=marker
    )
    plt.xlim(dims[0][0], dims[0][1])
    plt.ylim(dims[1][0], dims[1][1])