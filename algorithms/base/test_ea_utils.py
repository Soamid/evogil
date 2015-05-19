from unittest import TestCase
import itertools
import operator
from algorithms.utils.ea_utils import *
import problems.kursawe.problem as kursawe


class TestEAUtils(TestCase):
    def test_gen_population(self):
        dims = [
            [(-10, 10)],
            [(-10, 0), (0, 10)]
        ]
        for dm in dims:
            res = gen_population(10, dm)
            self.assertEqual(len(res), 10)
            for i in res:
                self.assertEqual(len(dm), len(dm))
                for (a, b), c in zip(dm, i):
                    self.assertTrue(a < c < b)

    def test_condition_count(self):
        self.assertEqual(len(list(condition_count(15))), 15)

    def test_condition_time(self):
        a = time.time()
        for _ in condition_time(t=0.5):
            b = time.time()
            self.assertTrue(b < a + 0.6)
        self.assertTrue(time.time() >= a + 0.5)

    def test_euclid_distance(self):
        self.assertEqual(euclid_sqr_distance([], []), 0.)
        self.assertEqual(euclid_sqr_distance([1], [1]), 0.)
        self.assertEqual(euclid_sqr_distance([1], [2]), 1.)
        self.assertEqual(euclid_sqr_distance([1], [3]), 4.)
        self.assertEqual(euclid_sqr_distance([1, 1], [1, 3]), 4.)
        self.assertEqual(euclid_sqr_distance([1, 1], [1, 3]), 4.)
        self.assertEqual(euclid_sqr_distance([0, 0, 0, 0], [1, 1, 1, 1]), 4.)

    def test_dominates(self):
        data = [
            ([0, 0], [1, 0], True),
            ([1, 1], [1, 1], False),
            ([1, 0], [0, 0], False),
        ]
        for a, b, c in data:
            self.assertEquals(dominates(a, b), c)

        indA = [-11.156972810852487, 2.761763183619566]
        indB = [-8.206139720524648, -7.529509725453117]
        self.assertEqual(0, domination_cmp(indA, indB))

    def test_domination_cmp(self):
        data = [
            ([0, 0], [1, 0], 1),
            ([1, 1], [1, 1], 0),
            ([1, 0], [0, 0], -1),
        ]
        for a, b, c in data:
            self.assertEquals(domination_cmp(a, b), c)


    def test_paretofront_layers(self):
        def identity(x):
            return [x]

        indvs = [[0, 0], [1, 1], [0, 1], [1, 0], [1, 1]]
        res = list(paretofront_layers(indvs, identity))
        self.assertEqual(sum(len(layer)
                             for layer in res),
                         len(indvs))
        self.assertListEqual(res[0], [[0, 0]])
        self.assertTrue([0, 1] in res[1])
        self.assertTrue([1, 0] in res[2])
        self.assertListEqual(res[3], [[1, 1], [1, 1]])

    def test_paretofront_layers_even_more(self):
        fitnesses = [lambda xs: (xs[0] - 2) ** 2, lambda xs: (xs[1] + 3) ** 2]

        def fits(xs):
            return [f(xs) for f in fitnesses]

        random.seed()
        mkd = lambda: random.choice([0, 1, 2, 3])
        #noinspection PyUnusedLocal
        pop = [[mkd() for j in range(3)]
               for i in range(1000)]
        res = paretofront_layers(pop, fits)
        ind_a = [2, 3, 2]
        ind_b = [2, 2, 1]
        self.assertNotEqual(0, domination_cmp(fits(ind_a), fits(ind_b)))
        self.assertNotEqual(0, domination_cmp(fits(ind_b), fits(ind_a)))
        for layer in res:
            for ind_a, ind_b in itertools.combinations(layer, 2):
                fa, fb = fits(ind_a), fits(ind_b)
                self.assertEqual(0, domination_cmp(fa, fb))
                self.assertEqual(0, domination_cmp(fa, fa))
                self.assertEqual(0, domination_cmp(fb, fb))
                self.assertFalse(dominates(fa, fb))
                self.assertFalse(dominates(fa, fa))
                self.assertFalse(dominates(fb, fb))

    def test_paretofront_layers_moremore(self):
        """ Previous tests were not enough, some errors did show in e.g. kursawe. """

        def mk_indiv():
            return [random.uniform(a, b) for a, b in kursawe.dims]

        def eval_fits(indiv):
            return indiv, [f(indiv) for f in kursawe.fitnesses]

        random.seed()
        pop = [eval_fits(mk_indiv()) for _ in range(400)]
        layers = paretofront_layers(pop, operator.itemgetter(1))
        for layA, layB in itertools.combinations(layers, 2):
            for indA_1, indA_2 in itertools.product(layA, repeat=2):
                try:
                    self.assertEqual(0, domination_cmp(indA_1[1], indA_2[1]))
                except AssertionError as e:
                    print("ERR!\n\nA = {0}\nB = {1}\nf(A) = {2}\nf(B) = {3}".format(indA_1[0],
                                                                                    indA_2[0],
                                                                                    indA_1[1],
                                                                                    indA_2[1]))
                    raise e
            for indA in layA:
                for indB in layB:
                    try:
                        self.assertFalse(dominates(indB[1], indA[1]))
                    except AssertionError as e:
                        print("ERR!\n\nA = {0}\nB = {1}\nf(A) = {2}\nf(B) = {3}".format(indA[0],
                                                                                        indB[0],
                                                                                        indA[1],
                                                                                        indB[1]))
                        raise e
