import unittest

#noinspection PyPep8Naming
import itertools
import algorithms.SPEA2.SPEA2 as spea2
from algorithms.utils import ea_utils
from problems.kursawe import problem

from problems.testrun import TestRun


#
#
# PyCharm Unittest runner setting: working directory set to Git-root (`evolutionary-pareto` dir).
#
#


#noinspection PyPep8Naming
class TestRunSPEA2(TestRun):
    alg_name = "spea2"

    @TestRun.skipByName()
    @TestRun.map_param('budget', range(500, 9500, 1000),
                       gather_function=TestRun.gather_function)
    def test_final(self, budget=None):
        self._run_test([0.8, 0.4, 0.2], 100, budget, itertools.count())


    def _run_test(self, var, popsize=100, budget=None, steps_gen=range(20)):
        init_population = ea_utils.gen_population(popsize, problem.dims)

        self.alg = spea2.SPEA2(dims=problem.dims,
                               population=init_population,
                               fitnesses=problem.fitnesses,
                               mutation_variance=var,
                               crossover_variance=var)
        self.run_alg(budget, problem, distribution_metrics_sigma=0.5)

if __name__ == '__main__':
    unittest.main()
