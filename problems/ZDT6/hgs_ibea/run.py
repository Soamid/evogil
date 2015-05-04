import functools
import unittest

#noinspection PyPep8Naming
import algorithms.hgs.hgs as hgs
#noinspection PyPep8Naming
import algorithms.ibea.ibea as ibea
from algorithms.utils import ea_utils
from problems.ZDT6 import problem

from problems.testrun import TestRun




class TestRunHGSwithIBEA(TestRun):
    alg_name = "hgs_ibea"

    @TestRun.skipByName()
    @TestRun.map_param('budget', range(500, 9500, 1000),
                       gather_function=TestRun.gather_function)
    def test_final(self, budget=None):
        self.alg = hgs.HGS.gen_finaltest(problem,
                                         functools.partial(ibea.IBEA,
                                                           kappa=0.05,
                                                           mating_population_size=0.5))
        self.run_alg(budget, problem)


if __name__ == '__main__':
    unittest.main()
