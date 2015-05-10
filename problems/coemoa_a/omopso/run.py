import logging
import unittest

# noinspection PyPep8Naming
from py4j.java_gateway import JavaGateway
import ep.omopso.omopso as omopso
from ep.utils import ea_utils
from problems.coemoa_a import problem

from problems.testrun import TestRun


#
#
# PyCharm Unittest runner setting: working directory set to Git-root (`evolutionary-pareto` dir).
#
#


class TestRunOMOPSO(TestRun):
    alg_name = "omopso"

    @TestRun.skipByName()
    @TestRun.map_param('budget', range(500, 9500, 1000),
                       gather_function=TestRun.gather_function)
    def test_normal(self, budget=None):
        init_population = ea_utils.gen_population(100, problem.dims)

        gateway = JavaGateway()

        logger = logging.getLogger("py4j")
        logger.setLevel(logging.ERROR)

        zdt1_problem = gateway.jvm.org.uma.jmetal.problem.multiobjective.zdt.ZDT1(len(problem.dims))

        self.alg = omopso.OMOPSO(gateway, zdt1_problem, 100, 100)

        self.run_alg(budget, problem)

        print(len(self.alg.finish()))


if __name__ == '__main__':
    unittest.main()
