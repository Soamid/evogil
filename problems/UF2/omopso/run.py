import unittest

#noinspection PyPep8Naming
import ep.omopso.omopso as omopso
from ep.utils import ea_utils
from problems.UF2 import problem

from problems.testrun import TestRun


#
#
# PyCharm Unittest runner setting: working directory set to Git-root (`evolutionary-pareto` dir).
#
#


class TestRunOMOPSO(TestRun):
    alg_name = "omopso"

    @TestRun.skipByName()
    @TestRun.map_param('budget', range(500, 9500, 1000),
                       gather_function=TestRun.gather_function)
    def test_normal(self, budget=None):
        init_population = ea_utils.gen_population(100, problem.dims)

        self.alg = omopso.OMOPSO(population=init_population,
                                 dims=problem.dims,
                                 fitnesses=problem.fitnesses,
                                 mutation_perturbation=0.5
                                 )
        self.run_alg(budget, problem)


if __name__ == '__main__':
    unittest.main()
