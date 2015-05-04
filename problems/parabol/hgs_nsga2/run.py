import functools
import unittest
import algorithms.hgs.hgs as hgs
import algorithms.nsga2.nsga2 as nsga2
from algorithms.utils import ea_utils
from problems.parabol import problem


# PyCharm Unittest runner setting: working directory set to Git-root (evolutionary-pareto)
from problems.testrun import TestRun


class TestRunHGSwithNSGA2(TestRun):
    alg_name = "hgs_nsga2"

    @TestRun.skipByName()
    @TestRun.with_gathering(TestRun.gather_function)
    def test_quick(self):
        self.problem_mod = problem
        self.comment = """*Szybki* test. Ma działać w granicach 1-3sek.
Służy do szybkiego sprawdzania, czy wszystko się ze sobą zgrywa."""

        init_population = ea_utils.gen_population(30, problem.dims)
        sclng_coeffs = [[20, 20], [5, 5], [1, 1]]
        self.alg = hgs.HGS.make_std(dims=problem.dims,
                                    population=init_population,
                                    fitnesses=problem.fitnesses,
                                    popln_sizes=[30, 15, 5],
                                    sclng_coeffss=sclng_coeffs,
                                    muttn_varss=hgs.HGS.make_sigmas(1, sclng_coeffs, problem.dims),
                                    csovr_varss=hgs.HGS.make_sigmas(1, sclng_coeffs, problem.dims),
                                    sprtn_varss=hgs.HGS.make_sigmas(0.7, sclng_coeffs, problem.dims),
                                    brnch_comps=[0.5, 0.125, 0.01],
                                    metaepoch_len=10,
                                    driver=functools.partial(nsga2.NSGA2, mating_population_size=0.5),
                                    stop_conditions=[])
        self.run_alg(None, problem, steps_gen=range(2))

if __name__ == '__main__':
    unittest.main()
