import unittest

#noinspection PyPep8Naming
import algorithms.HGS.HGS as hgs
#noinspection PyPep8Naming
import algorithms.SPEA2 as SPEA2
from evotools import ea_utils
from problems.ZDT2 import problem

from problems.testrun import TestRun




#noinspection PyPep8Naming
class TestRunHGSwithSPEA2(TestRun):
    alg_name = "hgs_spea2"

    @TestRun.skipByName()
    @TestRun.map_param('budget', range(500, 9500, 1000),
                       gather_function=TestRun.gather_function)
    def test_final(self, budget=None):
        self.alg = hgs.HGS.gen_finaltest(problem,
                                         SPEA2.SPEA2)
        self.run_alg(budget, problem)

if __name__ == '__main__':
    unittest.main()
