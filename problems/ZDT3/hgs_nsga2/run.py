import functools
import unittest

#noinspection PyPep8Naming
import algorithms.HGS.HGS as hgs
#noinspection PyPep8Naming
import algorithms.NSGAII.NSGAII as nsga2
from evotools import ea_utils
from problems.ZDT3 import problem

from problems.testrun import TestRun



#noinspection PyPep8Naming
class DisabledRunHGSwithNSGA2(): #TestRun):
    alg_name = "hgs_nsga2"

    @TestRun.skipByName()
    @TestRun.map_param('budget', range(500, 9500, 1000),
                       gather_function=TestRun.gather_function)
    def test_final(self, budget=None):
        self.alg = hgs.HGS.gen_finaltest(problem,
                                         functools.partial(nsga2.NSGAII,
                                                           mating_population_size=0.5))
        self.run_alg(budget, problem)

if __name__ == '__main__':
    unittest.main()
