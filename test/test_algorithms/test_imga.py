import unittest

from algorithms.base.drivergen import StepsRun
from simulation.run_parallel import prepare


class ImgaTest(unittest.TestCase):

    def test_imga(self):
        steps = [0, 1, 3]

        for steps_no in steps:
            with self.subTest(steps_no=steps_no):
                internal_driver, _ = prepare("NSGAII", "ZDT1")
                final_driver, problem_mod = prepare("IMGA", "ZDT1", internal_driver)
                print(final_driver())

                imga = final_driver()

                steps_run = StepsRun(steps_no)

                results = []
                steps_run.create_job(imga)\
                    .do_action(on_next=lambda x : print(x)) \
                    .subscribe(lambda proxy: results.append(proxy))

                print(results)
                self.assertEqual(len(results), steps_no)

