import unittest

#noinspection PyPep8Naming
import itertools
import ep.spea2.spea2 as spea2
from ep.utils import ea_utils
from problems.ackley import problem

from problems.testrun import TestRun


#
#
# PyCharm Unittest runner setting: working directory set to Git-root (`evolutionary-pareto` dir).
#
#


#noinspection PyPep8Naming
class TestRunSPEA2(TestRun):
    alg_name = "spea2"

    TestRun.selected_tests = -1

    @TestRun.skipByName()
    @TestRun.with_gathering(TestRun.gather_function)
    def test_quick(self):
        var = [abs(maxa-mina)/100
               for (mina, maxa) in problem.dims]
        self._run(75, var, range(3))


    @TestRun.skipByName()
    @TestRun.map_param('budget', range(50, 950, 100),
                       gather_function=TestRun.gather_function)
    def test_final(self, budget=None):
        var = [abs(maxa-mina)/100
               for (mina, maxa) in problem.dims]
        self._run(100, var, itertools.count(), budget)


    def _run(self, popsize, var, steps_gen, budget=None):
        init_population = ea_utils.gen_population(popsize, problem.dims)

        self.alg = spea2.SPEA2(dims=problem.dims,
                               population=init_population,
                               fitnesses=problem.fitnesses,
                               mutation_variance=var,
                               crossover_variance=var)
        self.run_alg(budget, problem, steps_gen)

if __name__ == '__main__':
    unittest.main()
