import unittest

#noinspection PyPep8Naming
import ep.nsga2.nsga2 as nsga2
from ep.utils import ea_utils
from problems.coemoa_c import problem

from problems.testrun import TestRun


#
#
# PyCharm Unittest runner setting: working directory set to Git-root (`evolutionary-pareto` dir).
#
#


#noinspection PyPep8Naming
class TestRunNSGA2(TestRun):
    alg_name = "nsga2"

    @TestRun.skipByName()
    @TestRun.map_param('budget', range(500, 9500, 1000),
                       gather_function=TestRun.gather_function)
    def test_quick(self, budget=None):
        init_population = ea_utils.gen_population(100, problem.dims)
        var = [abs(maxa-mina)/100
               for (mina, maxa) in problem.dims]
        self.alg = nsga2.NSGA2(population=init_population,
                               dims=problem.dims,
                               fitnesses=problem.fitnesses,
                               mutation_variance=var,
                               crossover_variance=var,
                               mating_population_size=0.5)
        self.run_alg(budget, problem)


if __name__ == '__main__':
    unittest.main()
