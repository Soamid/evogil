import functools
import unittest

#noinspection PyPep8Naming
import algorithms.HGS.HGS as hgs
#noinspection PyPep8Naming
import algorithms.IBEA.IBEA as ibea
from evotools import ea_utils
from problems.kursawe import problem

from problems.testrun import TestRun




class TestRunHGSwithIBEA(TestRun):
    alg_name = "hgs_ibea"

    @TestRun.skipByName()
    @TestRun.map_param('budget', range(500, 9500, 1000),
                       gather_function=TestRun.gather_function)
    def test_final(self, budget=None):
        self.alg = hgs.HGS.gen_finaltest(problem,
                                         functools.partial(IBEA.IBEA,
                                                           kappa=0.05,
                                                           mating_population_size=0.5))
        self.run_alg(budget, problem, distribution_metrics_sigma=0.5)


if __name__ == '__main__':
    unittest.main()
