import functools
import unittest

#noinspection PyPep8Naming
import ep.hgs.hgs as hgs
#noinspection PyPep8Naming
import ep.ibea.ibea as ibea
from ep.utils import ea_utils
from problems.ackley import problem

from problems.testrun import TestRun


#
#
# PyCharm Unittest runner setting: working directory set to Git-root (`evolutionary-pareto` dir).
#
#


class TestRunHGSwithIBEA(TestRun):
    alg_name = "hgs_ibea"

    @TestRun.skipByName()
    @TestRun.map_param('budget', range(50, 950, 100),
                       gather_function=TestRun.gather_function)
    def test_quick(self, budget=None):
        init_population = ea_utils.gen_population(20, problem.dims)
        sclng_coeffs = [[10, 10], [5, 5], [1, 1]]
        self.alg = hgs.HGS.make_std(dims=problem.dims,
                                    population=init_population,
                                    fitnesses=problem.fitnesses,
                                    popln_sizes=[len(init_population), 9, 5],
                                    sclng_coeffss=sclng_coeffs,
                                    muttn_varss=hgs.HGS.make_sigmas(20, sclng_coeffs, problem.dims),
                                    csovr_varss=hgs.HGS.make_sigmas(10, sclng_coeffs, problem.dims),
                                    sprtn_varss=hgs.HGS.make_sigmas(100, sclng_coeffs, problem.dims),
                                    brnch_comps=[0.5, 0.125, 0.01],
                                    metaepoch_len=5,
                                    max_children=2,
                                    driver=functools.partial(ibea.IBEA, kappa=0.05, mating_population_size=0.5),
                                    stop_conditions=[])
        self.run_alg(budget, problem)


if __name__ == '__main__':
    unittest.main()
