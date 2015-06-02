import unittest

# noinspection PyPep8Naming
import ep.thetansga3.thetansga3 as thetansga3
from ep.utils import ea_utils
from problems.coemoa_e import problem

from problems.testrun import TestRun


#
#
# PyCharm Unittest runner setting: working directory set to Git-root (`evolutionary-pareto` dir).
#
#


#noinspection PyPep8Naming
class TestRunThetaNSGA3(TestRun):
    alg_name = "theta-nsga3"

    @TestRun.skipByName()
    @TestRun.map_param('budget', range(500, 9500, 1000),
                       gather_function=TestRun.gather_function)
    def test_quick(self, budget=None):
        init_population = ea_utils.gen_population(100, problem.dims)

        self.alg = thetansga3.ThetaNSGAIII(population=init_population,
                                           dims=problem.dims,
                                           fitnesses=problem.fitnesses)
        self.run_alg(budget, problem)


if __name__ == '__main__':
    unittest.main()
