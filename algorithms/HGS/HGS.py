# coding=utf-8
from itertools import count
import logging
import random
from collections import deque
from contextlib import suppress

from algorithms.base.drivergen import DriverGen
from algorithms.base.driverlegacy import DriverLegacy
from algorithms.base.drivertools import average_indiv, rank
from evotools.metrics_utils import euclid_distance
from evotools.ea_utils import paretofront_layers, one_fitness
from evotools.random_tools import take



class HGS(DriverGen):
    # Kilka ustawień HGS-u
    global_branch_compare = False
    node_population_returns_only_front = False

    def __init__(self, dims, population, fitnesses, population_per_level, scaling_coefficients, crossover_variance,
                 sprouting_variance, mutation_variance, branch_comparison, metaepoch_len, driver, max_children,
                 mutation_probability=0.05, sproutiveness=1, driver_kwargs_per_level=None):
        """
        @type dims: list[(float,float)]  # dimensions' ranges, one per dimension
        @type population: list[list[float]]  # initial population
        @type fitnesses: list[(list[float], ) -> list[float]]  # fitness functions
        @type population_per_level: list[int]  # one per depth
        @type scaling_coefficients: list[float]  # scaling the universa, one per level
        @type crossover_variance: list[float]  # one per dimension
        @type sprouting_variance: list[float]  # one per dimension
        @type mutation_variance: list[float]  # one per dimension
        @type branch_comparison: float
        @type metaepoch_len: int  # length of the metaepoch
        @type driver: T <= DriverGen | T <= DriverLegacy
        @type max_children: int  # limit the number of immediate sprouts
        @type mutation_probability : float
        @type sproutiveness: int  # number of sprouts generated on each metaepoch
        @type driver_kwargs_per_level : list[dict]
        :rtype: HGS
        """
        if not driver_kwargs_per_level:
            driver_kwargs_per_level = [{} for _ in population_per_level]
        super().__init__()

        self.fitnesses = fitnesses
        self.dims = dims

        self.mutation_variance = mutation_variance
        self.mutation_probability = mutation_probability

        self.crossover_variance = crossover_variance

        self.sprouting_variance = sprouting_variance
        self.branch_comparison = branch_comparison

        self.scaling_coefficients = scaling_coefficients
        self.population_per_level = population_per_level
        self.dims_per_lvl = [
            [
                (0, (b - a) / coeff)
                for (a, b)
                in dims
            ]
            for coeff
            in self.scaling_coefficients
        ]
        self.fitnesses_per_lvl = [
            [
                lambda xs: fit(self.code(xs, lvl))
                for fit
                in self.fitnesses
                ]
            for lvl, _
            in enumerate(self.scaling_coefficients)
        ]
        self.driver_kwargs_per_level = driver_kwargs_per_level

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
        @type xs: list[float]
        @type lvl: int
        :rtype: list[float]
        """
        return [(x * self.scaling_coefficients[lvl] + a)
                for x, (a, b)
                in zip(xs,
                       self.dims)]

    def decode(self, xs, lvl):
        """ [a,b]^d -> U_l, l=1..m
        @type xs: list[float]
        @type lvl: int
        :return: list[float]
        """
        return [(x - a) / self.scaling_coefficients[lvl]
                for x, (a, b)
                in zip(xs,
                       self.dims)]

    def scale(self, xs, lvl):
        """ U_i -> U_{i+1}
        @type xs: list[float]
        @type lvl: int
        :return: list[float]
        """
        coeff_i = self.scaling_coefficients[lvl]
        coeff_j = self.scaling_coefficients[lvl + 1]
        return [x * coeff_i / coeff_j
                for x
                in xs]

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
            this_metaepoch_cost = sum(
                node_cost
                for node
                in self.get_nodes()
                for node_cost
                in take(self.metaepoch_len,
                        node.step_iter())
            )
            yield HGS.HGSProxy(this_metaepoch_cost,
                               self.get_nodes(include_finished=True))

    class HGSProxy(DriverGen.Proxy):
        def __init__(self, cost, all_nodes):
            """
            @type cost: int
            @type all_nodes: HGS.Node
            :rtype: HGS.HGSProxy
            """
            super().__init__(cost)
            self.all_nodes = all_nodes

        def assimilate_immigrants(self, emigrants):
            raise Exception("HGS does not support migrations")

        def deport_emigrants(self, immigrants):
            raise Exception("HGS does not support migrations")

        def current_population(self):
            return self.finalized_population()

        def finalized_population(self):
            return [
                p
                for n in self.all_nodes
                for p in n.population
                ]

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    class Node:

        def __init__(self, outer, level, population):
            """
            @type outer: HGS
            @type level: int
            @type population: list[list[float]]  # scaled population
            """
            self.outer = outer
            self.id = next(outer.id_cnt)
            self.metaepochs_ran = 0
            self.level = level
            self.sprouts = []
            self.reduced = False

            self.driver = outer.driver(population=population,
                                       dims=outer.dims_per_lvl[level],
                                       fitnesses=outer.fitnesses_per_lvl[level],
                                       mutation_variance=outer.mutation_variance,
                                       crossover_variance=outer.crossover_variance,
                                       **outer.driver_kwargs_per_level[level])
            """ :type : T <= DriverGen | DriverLegacy """

            if isinstance(self.driver, DriverGen):
                self.last_proxy = None
                """ :type : HGS.HGSProxy """

        def step_iter(self):
            if isinstance(self.driver, DriverGen):
                while True:
                    for self.last_proxy in take(self.outer.metaepoch_len,
                                                self.driver.population_generator()):
                        pass
                    self.sprout()
                    self.branch_reduction()
                    self.metaepochs_ran += 1
                    yield self.last_proxy.cost

            elif isinstance(self.driver, DriverLegacy):
                while True:
                    cost = self.driver.steps(range(self.outer.metaepoch_len))
                    self.sprout()
                    self.branch_reduction()
                    self.metaepochs_ran += 1
                    yield cost

        @property
        def average(self):
            return average_indiv(self._get_driver_pop())

        def _get_driver_pop(self):
            logger = logging.getLogger(__name__)
            if isinstance(self.driver, DriverLegacy):
                return self.driver.population
            elif isinstance(self.driver, DriverGen):
                if self.last_proxy:
                    return self.last_proxy.finalized_population()
                else:
                    logger.debug("Wow, last_proxy=%s and someone wanted the population. self=%s",
                                 self.last_proxy, self, stack_info=True)
                    return []

        @property
        def population(self):
            the_pop = self._get_driver_pop()
            """ :type : list[list[float]] """
            if HGS.node_population_returns_only_front:
                def evaluator(x):
                    return [f(x) for f in self.outer.fitnesses_per_lvl[self.level]]

                return [self.outer.code(p, lvl=self.level)
                        for p
                        in next(paretofront_layers(the_pop, evaluator))]
            else:
                return [self.outer.code(p, lvl=self.level)
                        for p
                        in the_pop]

        @property
        def finished(self):
            return self.reduced or (isinstance(self.driver, DriverLegacy) and self.driver.finished)

        def sprout(self):
            logger = logging.getLogger(__name__)
            with suppress(AttributeError):
                if self.driver.finished:
                    return
            if self.reduced:
                return
            if 1 + self.level >= len(self.outer.population_per_level):
                return
            if self.metaepochs_ran < 1:
                return

            sproutiveness = self.outer.sproutiveness
            if self.outer.max_children:
                sproutiveness = min(sproutiveness,
                                    self.outer.max_children - len(self.sprouts))

            candidates = None
            if isinstance(self.driver, DriverLegacy):
                candidates = iter(self.driver.get_indivs_inorder())
            elif isinstance(self.driver, DriverGen):
                candidates = iter(rank(self.last_proxy.finalized_population(),
                                       one_fitness(self.outer.fitnesses_per_lvl[self.level])))

            for candidate in take(sproutiveness, candidates):
                scaled_candidate = self.outer.scale(candidate, lvl=self.level)

                if any(euclid_distance(s.average, scaled_candidate)
                        < self.outer.branch_comparison
                       for s
                       in (iter(self.sprouts))):
                    # jeśli istnieje podobny sprout to bierzemy następnego kandydata
                    continue

                initial_population = [
                    [
                        min(max(a, (random.gauss(x, sigma))), b)
                        for x, (a, b), sigma
                        in zip(scaled_candidate,
                               self.outer.dims_per_lvl[self.level + 1],
                               self.outer.sprouting_variance)
                    ]
                    for _
                    in range(self.outer.population_per_level[self.level + 1])
                ]

                newnode = HGS.Node(self.outer, self.level + 1, initial_population)
                self.sprouts.append(newnode)
                logger.debug("sprouting: {a}:{aep} -> {b}".format(a=self.id, b=newnode.id,
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
                    if euclid_distance(a.average, b.average) < self.outer.branch_comparison:
                        b.reduced = True
