import unittest

# noinspection PyPep8Naming
import itertools
import ep.smsemoa.smsemoa as smsemoa
from ep.utils import ea_utils
from problems.coemoa_a import problem

from problems.testrun import TestRun


#
#
# PyCharm Unittest runner setting: working directory set to Git-root (`evolutionary-pareto` dir).
#
#


# noinspection PyPep8Naming
class TestRunSMSEMOA(TestRun):
    alg_name = "sms-emoa"


    @TestRun.skipByName()
    @TestRun.map_param('budget', range(500, 9500, 1000),
                       gather_function=TestRun.gather_function)
    def test_final(self, budget=None):
        self._run_test(100, itertools.count(), 0.1, budget)


    def _run_test(self, popsize, steps_gen, var_mult, budget=None):
        init_population = ea_utils.gen_population(popsize, problem.dims)

        var = [abs(maxa - mina) / var_mult
               for (mina, maxa) in problem.dims]

        reference_point = tuple(
            max(problem.pareto_front, key=lambda x: x[i])[i] for i in range(len(problem.pareto_front[0])))
        self.alg = smsemoa.SMSEMOA(dims=problem.dims,
                                   population=init_population,
                                   fitnesses=problem.fitnesses,
                                   mutation_variance=var,
                                   crossover_variance=var,
                                   reference_point=reference_point)
        self.run_alg(budget, problem)

        if __name__ == '__main__':
            unittest.main()
