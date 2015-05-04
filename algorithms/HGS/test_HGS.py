from unittest import TestCase

import inspect
import random
import time

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.mlab as ml

import benchmarks

from algorithms.utils import ea_utils
from algorithms.hgs.hgs import HGS
from algorithms.SGA.sga import SGA


#noinspection PyPep8Naming
class TestHGS(TestCase):
    def assertListAlmostEqual(self, xs, ys):
        try:
            for x, y in zip(xs, ys):
                self.assertAlmostEqual(x, y)
        except Exception as e:
            raise e  # ...and stop! Breakpoint time!

    def test_code_decode(self):
        fitnesses = [lambda xs: (xs[0] - 2) ** 2, lambda xs: (xs[1] + 3) ** 2]
        dims = [(5, 11), (-3, 19)]
        random.seed()
        init_population = [[random.uniform(a, b)
                            for (a, b) in dims]
                           for _ in range(1000)]
        a = HGS(dims=dims,
                population=init_population,
                fitnesses=fitnesses,
                lvl_params={'popln_size': [1, 1, 1],
                            'sclng_coeffs': [[3, 3], [2, 2], [1, 1]],
                            'csovr_var': [[3, 1.5], [1.5, 0.5]],
                            'muttn_var': [[], []],
                            'sprtn_var': [[], []],
                            'brnch_comp': [0.5, 0.1]},
                metaepoch_len=10,
                driver=SGA)
        print("Property: code_l ∘ decode_l = id")
        for individual in init_population:
            for level in range(3):
                self.assertListAlmostEqual(individual, a.code[level](a.decode[level](individual)))
        print("Property: code_(l+1) ∘ scale_l ∘ decode_l = id")
        for individual in init_population:
            for level in range(3 - 1):
                self.assertListAlmostEqual(individual, a.code[level + 1](a.scale[level](a.decode[level](individual))))
        print("Property: ∀ f ∈ fitnesses: f_l ∘ decode_l = f")
        for individual in init_population:
            for level in range(3):
                self.assertListAlmostEqual([f(individual) for f in fitnesses],
                                           [f(a.decode[level](individual)) for f in a.fitnesses_per_lvl[level]])

    def test_byhand(self):
        ind_a = [0, 0]
        ind_b = [1, 1]
        ind_c = [11, 2]
        ind_d = [3, 0]
        ind_e = [5, -1]
        population = [ind_a, ind_b, ind_c, ind_d, ind_e]
        fit_a = lambda xs: (xs[0] - 2) ** 2
        fit_b = lambda xs: (xs[1] + 3) ** 2
        fits = [fit_a, fit_b]
        a = HGS(dims=[(5, 11), (-1, 2)],
                population=population,
                fitnesses=fits,
                lvl_params={'popln_size': [5, 3, 1],
                            'sclng_coeffs': [[3, 3], [2, 2], [1, 1]],
                            'csovr_var': [[3, 1.5], [1.5, 0.5]],
                            'muttn_var': [[], []],
                            'sprtn_var': [[], []],
                            'brnch_comp': [0.5, 0.1]},
                metaepoch_len=10,
                driver=SGA,
                max_children=3,
                sproutiveness=1)

        enc_c0 = a.decode[0](ind_c)
        for i, j in zip(ind_c, a.code[0](enc_c0)):
            self.assertAlmostEqual(i, j)

        ind_c0 = a.code[1](a.scale[0](enc_c0))
        for i, j in zip(ind_c, ind_c0):
            self.assertAlmostEqual(i, j)

        fit_c0_a = [f(ind_c) for f in fits]
        fit_c0_b = [f(enc_c0) for f in a.fitnesses_per_lvl[0]]
        for i, j in zip(fit_c0_a, fit_c0_b):
            self.assertAlmostEqual(i, j)

    def test_sga_small(self):
        benchmark_tests = [benchmarks.parabol]
        # , benchmarks.kursawe,
        # benchmarks.emoa_a, benchmarks.emoa_b,
        # benchmarks.emoa_c, benchmarks.emoa_d]

        for fitnesses, dims, name, (solutionX, solutionY) in benchmark_tests:
            random.seed()

            print("{klass}.{fun} - {name}".format(klass=self.__class__.__name__,
                                                  fun=inspect.stack()[1][3],
                                                  **locals()))

            wall_time = -time.clock()

            hgs = HGS(dims=dims,
                      population=ea_utils.gen_population(count=100,
                                                         dims=dims),
                      fitnesses=fitnesses,
                      lvl_params={'popln_size': [100, 20, 5],
                                  'sclng_coeffs': [[100, 100], [30, 30], [1, 1]],
                                  'csovr_var': [[3, 1.5], [1.5, 0.5], [0.5, 0.125]],
                                  'muttn_var': [[3, 3], [2, 2], [0.5, 0.5]],
                                  'sprtn_var': [[1, 1], [0.5, 0.5], [0.1, 0.1]],
                                  'brnch_comp': [1, 0.5, 0.1]},
                      metaepoch_len=10,
                      driver=SGA,
                      max_children=3,
                      sproutiveness=1)
            hgs.steps(range(5))
            res = hgs.population
            wall_time += time.clock()

            plt.figure()
            plt.title("{klass}.{fun} - {name} co-domain(T: {wall_time:0.2f}s)".format(klass=self.__class__.__name__,
                                                                                      fun=inspect.stack()[0][3],
                                                                                      **locals()))
            plt.xlabel('1st objective')
            plt.ylabel('2nd objective')
            plt.scatter(solutionX, solutionY, c='r')
            plt.scatter([fitnesses[0](i) for i in res], [fitnesses[1](i) for i in res], c='b')
            plt.savefig("{klass}__{fun}__{name}__codomain.png".format(klass=self.__class__.__name__,
                                                                      fun=inspect.stack()[0][3],
                                                                      **locals()))

            co_res = ml.PCA(np.matrix(res))
            co_x = [np.array(m).reshape(-1)[0] for m in co_res.Y]
            co_y = [np.array(m).reshape(-1)[1] for m in co_res.Y]

            plt.figure()
            plt.title(
                "{klass}.{fun} - {name} domain(T: {wall_time:0.2f}s)".format(klass=self.__class__.__name__,
                                                                             fun=inspect.stack()[0][3],
                                                                             **locals()))
            plt.xlabel('')
            plt.ylabel('')
            plt.scatter(co_x, co_y, c='b')
            plt.savefig("{klass}__{fun}__{name}__domain.png".format(klass=self.__class__.__name__,
                                                                    fun=inspect.stack()[0][3],
                                                                    **locals()))
