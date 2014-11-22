import functools
import unittest
import ep.hgs.hgs as hgs
import ep.ibea.ibea as ibea
from ep.utils import ea_utils
from problems.parabol import problem


# PyCharm Unittest runner setting: working directory set to Git-root (evolutionary-pareto)
from problems.testrun import TestRun


class TestRunHGSwithIBEA(TestRun):
    alg_name = "hgs_ibea"

    @TestRun.skipByName()
    @TestRun.with_gathering(TestRun.gather_function)
    def test_quick(self):
        self.problem_mod = problem
        self.comment = """*Szybki* test. Ma działać w granicach 1-3sek.
Służy do szybkiego sprawdzania, czy wszystko się ze sobą zgrywa."""

        init_population = ea_utils.gen_population(3, problem.dims)
        sclng_coeffs = [[4, 4], [2, 2], [1, 1]]
        self.alg = hgs.HGS.make_std(dims=problem.dims,
                                    population=init_population,
                                    fitnesses=problem.fitnesses,
                                    popln_sizes=[len(init_population), 2, 1],
                                    sclng_coeffss=sclng_coeffs,
                                    muttn_varss=hgs.HGS.make_sigmas(20, sclng_coeffs, problem.dims),
                                    csovr_varss=hgs.HGS.make_sigmas(10, sclng_coeffs, problem.dims),
                                    sprtn_varss=hgs.HGS.make_sigmas(100, sclng_coeffs, problem.dims),
                                    brnch_comps=[0.5, 0.125, 0.01],
                                    metaepoch_len=1,
                                    max_children=2,
                                    driver=functools.partial(ibea.IBEA, kappa=0.25, mating_population_size=5),
                                  stop_conditions=[])
        self.run_alg(None, problem, steps_gen=range(5))


if __name__ == '__main__':
    unittest.main()
