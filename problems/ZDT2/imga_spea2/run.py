import unittest

#noinspection PyPep8Naming
import algorithms.imga.imga as imga
from algorithms.spea2 import spea2
from algorithms.utils import ea_utils
from problems.ZDT2 import problem

from problems.testrun import TestRun


#
#
# PyCharm Unittest runner setting: working directory set to Git-root (`evolutionary-pareto` dir).
#
#


class TestRunIMGAWithSPEA2(TestRun):
    alg_name = "imga_spea2"

    @TestRun.skipByName()
    @TestRun.map_param('budget', range(500, 9500, 1000),
                       gather_function=TestRun.gather_function)
    def test_normal(self, budget=None):
        init_population = ea_utils.gen_population(100, problem.dims)
        var = [abs(maxa - mina) / 0.1
               for (mina, maxa) in problem.dims]

        self.alg = imga.IMGA(population=init_population,
                             dims=problem.dims,
                             fitnesses=problem.fitnesses,
                             mutation_variance=var,
                             crossover_variance=var,
                             islands_number=3,
                             migrants_number=5,
                             epoch_length=5,
                             driver=spea2.SPEA2
        )
        self.run_alg(budget, problem)


if __name__ == '__main__':
    unittest.main()