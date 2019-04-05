import unittest

import rx.operators as ops
from rx.concurrency import NewThreadScheduler

from algorithms.base.driver import StepsRun
from simulation.factory import prepare


class ImgaTest(unittest.TestCase):

    def test_results_number_is_correct(self):
        steps = [0, 1, 3]

        for steps_no in steps:
            with self.subTest(steps_no=steps_no):
                final_driver, problem_mod = prepare("IMGA+NSGAII", "ZDT1")
                print(final_driver())

                imga = final_driver()

                steps_run = StepsRun(steps_no)

                results = []
                steps_run.create_job(imga) \
                    .subscribe(lambda proxy: results.append(proxy))

                self.assertEqual(len(results), steps_no)

    def test_imga_cost_calculation(self):
        final_driver, problem_mod = prepare("IMGA+NSGAII", "ZDT1")

        imga = final_driver()

        steps_run = StepsRun(4)

        total_costs = []
        islands_costs = []

        def on_imga_result(result):
            total_costs.append(result.cost),
            islands_costs.append(sum([island.driver.cost for island in imga.islands]))

        steps_run.create_job(imga).pipe(
            ops.subscribe_on(NewThreadScheduler()),
            ops.do_action(on_next=on_imga_result)
        ).run()

        self.assertListEqual(total_costs, islands_costs)
