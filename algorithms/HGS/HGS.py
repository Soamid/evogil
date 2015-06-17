# coding=utf-8
from functools import partial
from itertools import count
import random
from collections import deque
from contextlib import suppress

from algorithms.base.drivergen import DriverGen
from algorithms.base.driverlegacy import DriverLegacy
from evotools.metrics import euclid_distance
from evotools.ea_utils import paretofront_layers
from evotools.random_tools import take
from evotools.stats import average


class HGS(DriverGen):
    # Kilka ustawień HGS-u
    global_branch_compare = False
    global_sprout_test = False
    node_population_returns_only_front = False

    def __init__(self, dims, population, fitnesses, scaling_coefficients, crossover_variance, mutation_variance,
                 sprouting_variance, population_per_level, metaepoch_len, driver, mutation_probability=0.05,
                 max_children=3, sproutiveness=1):
        """
        :param dims: list[(float,float)]  # dimensions' ranges, one per dimension
        :param population: list[list[float]]  # initial population
        :param fitnesses: list[(list[float], ) -> list[float]]  # fitness functions
        :param scaling_coefficients: list[float]  # scaling the universa, one per level
        :param crossover_variance: list[float]  # one per dimension
        :param mutation_variance: list[float]  # one per dimension
        :param sprouting_variance: list[float]  # one per dimension
        :param population_per_level: list[int]  # one per depth
        :param metaepoch_len: int  # length of the metaepoch
        :param driver: T <= DriverGen | T <= DriverLegacy
        :param max_children: int  # limit the number of immediate sprouts
        :param sproutiveness: int  # number of sprouts generated on each metaepoch
        :return: HGS
        """
        super().__init__()

        self.fitnesses = fitnesses
        self.dims = dims

        self.mutation_variance = mutation_variance
        self.mutation_probability = mutation_probability

        self.crossover_variance = crossover_variance

        self.sprouting_variance = sprouting_variance

        self.scaling_coefficients = scaling_coefficients
        self.population_per_level = population_per_level
        self.dims_per_lvl = [[(0, (b - a) / n) for n, (a, b) in zip(coeffs, dims)]
                             for coeffs in self.scaling_coefficients]

        self.sproutiveness = sproutiveness
        self.max_children = max_children
        self.metaepoch_len = metaepoch_len

        self.driver = driver

        self.id_cnt = count()  # counter for sprouts
        self.root = HGS.Node(self,
                             level=0,
                             population=[self.decode(p, lvl=0)
                                         for p in population])

    def code(self, xs, lvl):
        """ U_l -> [a,b]^d, l=1..m
        :param xs: list[float]
        :param lvl: int
        :rtype: list[float]
        """
        return [(x * n + a)
                for x, n, (a, b)
                in zip(xs,
                       self.scaling_coefficients[lvl],
                       self.dims)]

    def decode(self, xs, lvl):
        """ [a,b]^d -> U_l, l=1..m
        :param xs: list[float]
        :param lvl: int
        :return: list[float]
        """
        return [(x - a) / n
                for x, n, (a, b)
                in zip(xs,
                       self.scaling_coefficients[lvl],
                       self.dims)]

    def scale(self, xs, lvl):
        """ U_i -> U_{i+1}
        :param xs: list[float]
        :param lvl: int
        :return: list[float]
        """
        coeff_i = self.scaling_coefficients[lvl]
        coeff_j = self.scaling_coefficients[lvl+1]
        return [x * ni / nj
                for x, ni, nj
                in zip(xs,
                       coeff_i,
                       coeff_j)]

    def level_fitnesses(self, xs, lvl):
        """ U_l -> objectives
        :param xs: list[float]  # domain,
        :param lvl: int
        :return: list[float]  # co-domain
        """
        return [f(self.code(xs, lvl))
                for f
                in self.fitnesses]

    def get_nodes(self, include_finished=False):
        """ HGS nodes in level-order. """
        deq = deque([self.root])

        with suppress(IndexError):
            while True:
                x = deq.popleft()
                deq.extend(x.sprouts)
                if not x.finished or include_finished:
                    yield x

    def population_generator(self):
        while True:
            this_metaepoch_cost = \
                sum(  # sum the cost for all nodes
                    sum(  # sum the cost for all iterations of each node
                        node_cost
                        for node_cost, node_population
                        in take(self.metaepoch_len,
                                i.step_iter())
                    )
                    for i
                    in self.get_nodes()
                )
            yield HGS.HGSProxy(this_metaepoch_cost,
                               self.get_nodes(include_finished=True))

    class HGSProxy(DriverGen.Proxy):
        def __init__(self, cost, all_nodes):
            """
            :param cost: int
            :param all_nodes: list[Node]
            :return: HGSProxy
            """
            super().__init__(cost)
            self.all_nodes = all_nodes

        def send_emigrants(self, emigrants):
            raise Exception("HGS does not support migrations")

        def get_immigrants(self):
            raise Exception("HGS does not support migrations")

        def finalized_population(self):
            return [
                p
                for n in self.all_nodes
                for p in n.population
            ]

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    class Node:

        def __init__(self, outer, level, population):
            """
            :param outer: HGS
            :param level: int
            :param population: list[list[float]]  # scaled population
            :return:
            """
            self.outer = outer
            self.id = next(outer.id_cnt)
            self.metaepochs_ran = 0
            self.level = level
            self.sprouts = []
            self.reduced = False

            self.driver = outer.driver(population=population,
                                       dims=outer.dims_per_lvl[level],
                                       # fitnesses=partial(outer.level_fitnesses, lvl=level)
                                       fitnesses=outer.fitnesses_per_lvl[level],  # !!!!
                                       mutation_variance=outer.mutation_variance,
                                       mutation_probability=outer.mutation_probability,
                                       crossover_variance=outer.crossover_variance)

        def step_iter(self):
            if isinstance(self.driver, DriverGen):
                for proxy in self.driver.population_generator():
                    self.sprout()
                    self.branch_reduction()
                    self.metaepochs_ran += 1
                    yield proxy.cost

            elif isinstance(self.driver, DriverLegacy):
                driver_step_iterator = self.driver.steps()
                while True:
                    i = next(driver_step_iterator)
                    self.sprout()
                    self.branch_reduction()
                    self.metaepochs_ran += 1
                    yield i

        @property
        def average(self):
            #return average(self.driver.population)
            return self.driver.average

        @property
        def population(self):
            if HGS.node_population_returns_only_front:
                def evaluator(x):
                    return [f(x) for f in self.outer.fitnesses_per_lvl[self.level]]

                pareto_front = paretofront_layers(self.driver.population, evaluator)
                if len(pareto_front) > 0:
                    pareto_front = pareto_front[0]
                return (self.outer.code[self.level](p)
                        for p in pareto_front)
            return (self.outer.code[self.level](p)
                    for p in self.driver.population)

        @property
        def finished(self):
            return self.reduced or self.driver.finished

        def sprout(self):
            if self.driver.finished:
                return
            if self.reduced:
                return
            if 1 + self.level >= len(self.outer.popln_size):
                return
            if self.metaepochs_ran < 1:
                return

            sproutiveness = self.outer.sproutiveness
            if self.outer.max_children:
                sproutiveness = min(sproutiveness, self.outer.max_children - len(self.sprouts))

            candidates = iter(self.driver.get_indivs_inorder())
            for _ in range(sproutiveness):
                for candidate in candidates:
                    scaled_candidate = self.outer.scale[self.level](candidate)

                    # TL;DR: jeśli porównujemy globalnie to sprawdź, czy jakikolwiek ze sproutów
                    # na tym samym poziomie jest podobny. Wpp porównaj tylko ze sproutami-braćmi.
                    if HGS.global_sprout_test:
                        search_space = (s for n in self.outer.get_nodes() if n.level == self.level
                                        for s in n.sprouts)
                    else:
                        search_space = iter(self.sprouts)

                    if any(euclid_distance(s.average, scaled_candidate) < self.outer.brnch_cmp_c[self.level + 1]
                           for s in search_space):
                        # jeśli istnieje podobny sprout to bierzemy następnego kandydata
                        continue

                    initial_population = [[min(max(a, (random.gauss(x, sigma))), b)
                                           for x, (a, b), sigma in zip(scaled_candidate,
                                                                       self.outer.dims_per_lvl[self.level],
                                                                       self.outer.sprtn_vars[self.level])]
                                          for _ in range(self.outer.popln_size[self.level + 1])]
                    newnode = HGS.Node(self.outer, self.level + 1, initial_population)
                    self.sprouts.append(newnode)
                    print("  #    HGS>>> sprouting: {a}:{aep} -> {b}".format(a=self.id, b=newnode.id,
                                                                             aep=self.metaepochs_ran))
                    break

        def branch_reduction(self):
            if HGS.global_branch_compare:
                comparab_sprouts = list(self.outer.get_nodes(include_finished=True))
            else:
                comparab_sprouts = self.sprouts

            for i, a in enumerate(comparab_sprouts):
                if a.finished:
                    continue
                for b in comparab_sprouts[i + 1:]:
                    if a.level != b.level or b.finished:
                        continue
                    if euclid_distance(a.average, b.average) < self.outer.brnch_cmp_c[a.level]:
                        b.reduced = True
