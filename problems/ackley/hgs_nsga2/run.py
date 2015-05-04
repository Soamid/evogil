import functools
import unittest

#noinspection PyPep8Naming
import algorithms.hgs.hgs as hgs
#noinspection PyPep8Naming
import algorithms.nsga2.nsga2 as nsga2
from algorithms.utils import ea_utils
from problems.ackley import problem

from problems.testrun import TestRun


#
#
# PyCharm Unittest runner setting: working directory set to Git-root (`evolutionary-pareto` dir).
#
#


#noinspection PyPep8Naming
class TestRunHGSwithNSGA2(TestRun):
    alg_name = "hgs_nsga2"

    @TestRun.skipByName()
    @TestRun.map_param('budget', range(50, 950, 100),
                       gather_function=TestRun.gather_function)
    def test_quick(self, budget=None):
        init_population = ea_utils.gen_population(75, problem.dims)
        sclng_coeffs = [[4, 4, 4], [2, 2, 2], [1, 1, 1]]
        self.alg = hgs.HGS.make_std(dims=problem.dims,
                                    population=init_population,
                                    fitnesses=problem.fitnesses,
                                    popln_sizes=[len(init_population), 10, 5],
                                    sclng_coeffss=sclng_coeffs,
                                    muttn_varss=hgs.HGS.make_sigmas(20, sclng_coeffs, problem.dims),
                                    csovr_varss=hgs.HGS.make_sigmas(10, sclng_coeffs, problem.dims),
                                    sprtn_varss=hgs.HGS.make_sigmas(100, sclng_coeffs, problem.dims),
                                    brnch_comps=[0.05, 0.25, 0.01],
                                    metaepoch_len=1,
                                    max_children=2,
                                    driver=functools.partial(nsga2.NSGA2, mating_population_size=0.5),
                                    stop_conditions=[])
        self.run_alg(budget, problem)


if __name__ == '__main__':
    unittest.main()
