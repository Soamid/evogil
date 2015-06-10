import functools
import unittest

#noinspection PyPep8Naming
import ep.hgs.hgs as hgs
#noinspection PyPep8Naming
import ep.omopso.omopso as omopso
from ep.utils import ea_utils
from problems.coemoa_a import problem

from problems.testrun import TestRun



#noinspection PyPep8Naming
class TestRunHGSwithOMOPSO(TestRun):
    alg_name = "hgs_omopso"

    @TestRun.skipByName()
    @TestRun.map_param('budget', range(500, 9500, 1000),
                       gather_function=TestRun.gather_function)
    def test_final(self, budget=None):
        self.alg = hgs.HGS.gen_finaltest(problem,
                                         functools.partial(omopso.OMOPSO,
                                                           mutation_perturbation=0.5))
        self.run_alg(budget, problem)

if __name__ == '__main__':
    unittest.main()
