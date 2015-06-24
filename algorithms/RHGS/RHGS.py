import functools
import math
import random

from evotools.metrics_utils import euclid_distance
from evotools.ea_utils import paretofront_layers, gen_population, one_fitness
from evotools.random_tools import take

from algorithms.base.driverlegacy import DriverLegacy
from algorithms.base.drivertools import average_indiv, rank


class RHGS(DriverLegacy):
    # Kilka ustawień RHGS-u
    global_branch_compare = False
    global_sprout_test = False
    node_population_returns_only_front = False

    @staticmethod
    def make_sigmas(sigma, sclng_coeffs, dims):
        return [
            [sigma * (abs(b - a) / n) ** (1. / len(dims))  # n-ty pierwiastek z rozmiaru wymiaru, n to ilość wymiarów
             for (a, b), n in zip(dims, ns)]
            for ns in sclng_coeffs]

    @classmethod
    def make_std(cls,
                 dims:             ':: [ (Float, Float) ]',
                 population:       ':: Population',
                 fitnesses:        ':: [FitnessFun]',
                 popln_sizes:      ':: [Int]',
                 sclng_coeffss:    ':: [[Float]], -- po jednym na wymiar',
                 csovr_varss:      ':: [[Float]], -- po jednym na wymiar',
                 muttn_varss:      ':: [[Float]], -- po jednym na wymiar',
                 sprtn_varss:      ':: [[Float]], -- po jednym na wymiar',
                 brnch_comps:      ':: [Float]',
                 metaepoch_len:    ':: Int',
                 driver:           ':: Driver d => {fitnesses :: [FitnessFun], population :: Population} -> d',
                 stop_conditions:  ':: [(RHGS -> State RHGS ())]',
                 max_children:     ':: Int'=5,
                 sproutiveness:    ':: Int'=2):
        return cls(dims=dims,
                   population=population,
                   fitnesses=fitnesses,
                   lvl_params={'popln_sizes': popln_sizes,
                               'sclng_coeffss': sclng_coeffss,
                               'csovr_varss': csovr_varss,
                               'muttn_varss': muttn_varss,
                               'sprtn_varss': sprtn_varss,
                               'brnch_comps': brnch_comps
                   },
                   metaepoch_len=metaepoch_len,
                   driver=driver,
                   stop_conditions=stop_conditions,
                   max_children=max_children,
                   sproutiveness=sproutiveness)

    @staticmethod
    def gen_finaltest(problem, driver):
        sclng_coeffs = [[10, 10, 10], [2.5, 2.5, 2.5], [1, 1, 1]]
        pop_sizes = [50, 12, 4]
        return RHGS.make_std(dims=problem.dims,
                            population=gen_population(pop_sizes[0], problem.dims),
                            fitnesses=problem.fitnesses,
                            popln_sizes=pop_sizes,
                            sclng_coeffss=sclng_coeffs,
                            muttn_varss=RHGS.make_sigmas(20, sclng_coeffs, problem.dims),
                            csovr_varss=RHGS.make_sigmas(10, sclng_coeffs, problem.dims),
                            sprtn_varss=RHGS.make_sigmas(100, sclng_coeffs, problem.dims),
                            brnch_comps=[1, 0.25, 0.05],
                            metaepoch_len=1,
                            max_children=3,
                            driver=driver,
                            stop_conditions=[])

    def __init__(self,

                 mutation_variance,
                 crossover_variance,
                 sprouting_variance,

                 dims:             ':: [ (Float, Float) ]',
                 population:       ':: Population',
                 fitnesses:        ':: [FitnessFun]',
                 lvl_params:       ':: {popln_sizes   :: [Int],'
                                   '    sclng_coeffss :: [[Float]], -- po jednym na wymiar'
                                   '    csovr_varss   :: [[Float]], -- po jednym na wymiar'
                                   '    muttn_varss   :: [[Float]], -- po jednym na wymiar'
                                   '    sprtn_varss   :: [[Float]], -- po jednym na wymiar'
                                   '    brnch_comps   :: [Float]}'
                                   '-- |popln_size| = m, number of levels',
                 metaepoch_len:    ':: Int',
                 driver:           ':: Driver d => {fitnesses :: [FitnessFun], population :: Population} -> d',
                 stop_conditions:  ':: [(RHGS -> State RHGS ())]',
                 max_children:     ':: Int'=3,
                 sproutiveness:    ':: Int'=1,):

        super().__init__(fitnesses=None,
                         dims=dims,
                         mutation_variance=None,
                         crossover_variance=None,
                         population=None)

        self.budget = -1
        self.id_cnt = 0

        self.sproutiveness = sproutiveness
        self.max_children = max_children
        self.metaepoch_len = metaepoch_len
        self.stop_conditions = stop_conditions
        self.driver = driver

        self.last_proxy = None

        self.popln_size = [len(population)] + lvl_params['popln_sizes'][1:]
        self.sclng_coeffs = [[x for _ in dims] for x in lvl_params['sclng_coeffss']]
        self.csvrs_vars = RHGS.make_sigmas(lvl_params['csovr_varss'], self.sclng_coeffs, dims)
        self.muttn_vars = RHGS.make_sigmas(lvl_params['muttn_varss'], self.sclng_coeffs, dims)
        self.sprtn_vars = RHGS.make_sigmas(lvl_params['sprtn_varss'], self.sclng_coeffs, dims)
        self.brnch_cmp_c = lvl_params['brnch_comps']

        # UWAGA na oznaczenia! Oryg. funkcje fitness operują na przestrzeni [a,b]^d, natomiast
        # RHGS sobie wszystko skaluje do U_l (zależnych od poziomu).

        def encode_ind(xs, ns, ds):  # U_l -> [a,b]^d, l=1..m
            nss = [ns[0] for _ in xs]
            # print("XS", len(xs))
            # print("NS", len(nss))
            # print("DS", len(ds))
            # print("ZIP", len([x for x in zip(xs, nss, ds)]))
            return [(x * n + a) for x, n, (a, b) in zip(xs, nss, ds)]

        self.code = [functools.partial(encode_ind, ns=coeffs, ds=dims) for coeffs in self.sclng_coeffs]

        def decode_ind(xs, ns, ds):  # [a,b]^d -> U_l, l=1..m
            nss = [ns[0] for _ in xs]
            # print("D XS", len(xs))
            # print("D NS", len(nss))
            # print("D DS", len(ds))
            # print("D ZIP", len([x for x in zip(xs, nss, ds)]))
            return [(x - a) / n for x, n, (a, b) in zip(xs, nss, ds)]

        self.decode = [functools.partial(decode_ind, ns=coeffs, ds=dims) for coeffs in self.sclng_coeffs]

        def scale_ind(xs, nsa, nsb):  # U_i -> U_{i+1}
            return [x * ni / nj for x, ni, nj in zip(xs, nsa, nsb)]

        self.scale = [functools.partial(scale_ind, nsa=cfa, nsb=cfb)
                      for cfa, cfb in zip(self.sclng_coeffs, self.sclng_coeffs[1:])]

        def fitness_decorated(xs, encoding_f, f):
            # print("LEN DIMS", len(self.dims))
            # print("LEN", len(xs))
            # print("ENCODING LEN " + str(len(encoding_f(xs))))
            return f(encoding_f(xs))

        self.fitnesses_per_lvl = [[functools.partial(fitness_decorated, f=f, encoding_f=codef)
                                   for f in fitnesses]
                                  for codef in self.code]

        self.dims_per_lvl = [[(0, (b - a) / n)
                              for n, (a, b) in zip(coeffs, dims)]
                             for coeffs in self.sclng_coeffs]

        self.root = RHGS.Node(self, 0, [self.decode[0](p)
                                       for p in population])
        self.root.metaepochs_ran = 0

    @property
    def population(self):
        return [p
                for n in self.get_nodes(include_finished=True)
                for p in n.population]

    def get_nodes(self, include_finished=False):
        """ Przechodzi drzewo RHGS w kolejności level-order. """
        todo = [self.root]
        while len(todo) > 0:
            if not todo[0].finished or include_finished:
                yield todo[0]
            todo = todo[1:] + todo[0].sprouts

    def steps(self, gen, budget=None):
        self.budget = budget
        cost = 0
        for _ in gen:
            if budget is not None and cost > budget:
                return cost
            cost += self.metaepoch()
            for stop_f in self.stop_conditions:
                stop_f(hgs=self, root=self.root)
                if self.finished:
                    return cost
        return cost

    def metaepoch(self):
        def cost_fun(cs):
            n = 3
            cs_rsort = sorted(cs, reverse=True)
            target = math.ceil(sum(cs) * 1.0 / 3)
            target_max = 0
            for i in range(n):
                subtarget = 0
                while cs_rsort and subtarget < target:
                    subtarget += cs_rsort.pop()
                target_max = max(subtarget, target_max)
            return math.ceil(target_max * 1.2)  # 1.2 to współczynnik pesymizmu. TODO: Gdy nastąpi poniedziałek zmienić na 1.3.
        cost = []
        for i in self.get_nodes():
            if not i.finished:
                #TODO ogarnac nowe drivery
                cost_iter = 0
                    # note to self: don't EVER code in python w/o tests
                for last_proxy in take(self.metaepoch_len,
                                            i.driver_generator):
                    self.last_proxy = last_proxy
                    i.last_proxy = last_proxy
                    cost_iter += self.last_proxy.cost
                cost.append(cost_iter)
                i.metaepochs_ran += 1
            if i.metaepochs_ran < 0:
                i.metaepochs_ran = 0
            i.sprout()
            i.branch_reduction()
            cost_fun_res = sum(cost)
            if self.budget and self.budget < cost_fun_res:
                return cost_fun_res
        return cost_fun(cost)

    def rank(self, population):
        return rank(population)

    def finish(self):
        return self.population

    #- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    class Node:

        def __init__(self,
                     outer:      ':: RHGS',
                     level:      ':: Int',
                     population: ':: ScaledPopulation'):
            self.outer = outer
            self.id, self.outer.id_cnt = self.outer.id_cnt, self.outer.id_cnt + 1
            self.metaepochs_ran = -1
            self.level = level
            self.sprouts = []
            self.reduced = False

            self.driver = outer.driver(population=population,
                                       dims=outer.dims_per_lvl[level],
                                       fitnesses=outer.fitnesses_per_lvl[level],
                                       mutation_variance=outer.muttn_vars[level],
                                       crossover_variance=outer.csvrs_vars[level])
            self.driver_generator = self.driver.population_generator()
            self.last_proxy = None

        @property
        def average(self):
            return average_indiv(self._get_driver_pop())

        def _get_driver_pop(self):
            if self.last_proxy:
                return self.last_proxy.finalized_population()
            else:
                return []

        @property
        def population(self):
            if self.last_proxy:
                pop = self.last_proxy.finalized_population()
            else:
                pop = []

            if RHGS.node_population_returns_only_front:
                def evaluator(x):
                    return [f(x) for f in self.outer.fitnesses_per_lvl[self.level]]

                #TODO zamiast population z dupy, to przez proxy
                pareto_front = paretofront_layers(pop, evaluator)
                if len(pareto_front) > 0:
                    pareto_front = pareto_front[0]
                return (self.outer.code[self.level](p)
                        for p in pareto_front)
            return (self.outer.code[self.level](p)
                    #TODO zamiast population z dupy, to przez proxy
                    for p in pop)

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
            if self.metaepochs_ran <= 0:
                return

            sproutiveness = self.outer.sproutiveness
            if self.outer.max_children:
                sproutiveness = min(sproutiveness, self.outer.max_children - len(self.sprouts))

            #TODO tego też już chyyyyba nie ma
            if self.last_proxy:
                pop = self.last_proxy.finalized_population()
            else:
                pop = []

            candidates = iter(rank(pop, one_fitness(self.outer.fitnesses_per_lvl[self.level])))
            for _ in range(sproutiveness):
                for candidate in candidates:
                    scaled_candidate = self.outer.scale[self.level](candidate)

                    # TL;DR: jeśli porównujemy globalnie to sprawdź, czy jakikolwiek ze sproutów
                    # na tym samym poziomie jest podobny. Wpp porównaj tylko ze sproutami-braćmi.
                    if RHGS.global_sprout_test:
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
                    newnode = RHGS.Node(self.outer, self.level + 1, initial_population)
                    self.sprouts.append(newnode)
                    print("  #    RHGS>>> sprouting: {a}:{aep} -> {b}".format(a=self.id, b=newnode.id,
                                                                             aep=self.metaepochs_ran))
                    break

        def branch_reduction(self):
            if RHGS.global_branch_compare:
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
