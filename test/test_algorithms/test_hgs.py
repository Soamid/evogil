import unittest

from algorithms.base.driver import StepsRun
from simulation.factory import prepare


class HGSTest(unittest.TestCase):
    def test_steps(self):
        final_driver, problem_mod = prepare("HGS+NSGAII", "ZDT1")
        print(final_driver())

        hgs = final_driver()

        steps = [0, 1, 3]

        for steps_no in steps:
            with self.subTest(steps_no=steps_no):
                steps_run = StepsRun(steps_no)

                results = []
                steps_run.create_job(hgs).subscribe(
                    lambda result: results.append(result)
                )

                self.assertEqual(len(results), steps_no)
