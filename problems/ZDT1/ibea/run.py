import unittest

#noinspection PyPep8Naming
import algorithms.IBEA.IBEA as ibea
from algorithms.utils import ea_utils
from problems.ZDT1 import problem

from problems.testrun import TestRun


#
#
# PyCharm Unittest runner setting: working directory set to Git-root (`evolutionary-pareto` dir).
#
#


class TestRunIBEA(TestRun):
    alg_name = "ibea"

    @TestRun.skipByName()
    @TestRun.map_param('budget', range(500, 9500, 1000),
                       gather_function=TestRun.gather_function)
    def test_normal(self, budget=None):
        init_population = ea_utils.gen_population(100, problem.dims)
        var = [abs(maxa-mina)/100
               for (mina, maxa) in problem.dims]
        self.alg = ibea.IBEA(population=init_population,
                             dims=problem.dims,
                             fitnesses=problem.fitnesses,
                             mutation_variance=var,
                             crossover_variance=var,
                             kappa=0.05,
                             mating_population_size=0.5)
        self.run_alg(budget, problem)


if __name__ == '__main__':
    unittest.main()
