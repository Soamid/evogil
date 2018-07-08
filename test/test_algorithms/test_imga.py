import unittest

from rx.concurrency import NewThreadScheduler

from algorithms.base.drivergen import StepsRun
from simulation.run_parallel import prepare


class ImgaTest(unittest.TestCase):

    def test_results_number_is_correct(self):
        steps = [0, 1, 3]

        for steps_no in steps:
            with self.subTest(steps_no=steps_no):
                internal_driver, _ = prepare("NSGAII", "ZDT1")
                final_driver, problem_mod = prepare("IMGA", "ZDT1", internal_driver)
                print(final_driver())

                imga = final_driver()

                steps_run = StepsRun(steps_no)

                results = []
                steps_run.create_job(imga) \
                    .subscribe(lambda proxy: results.append(proxy))

                self.assertEqual(len(results), steps_no)

    def test_imga_cost_calculation(self):
        internal_driver, _ = prepare("NSGAII", "ZDT1")
        final_driver, problem_mod = prepare("IMGA", "ZDT1", internal_driver)

        imga = final_driver()

        steps_run = StepsRun(4)

        total_costs = []
        islands_costs = []
        for result in steps_run.create_job(imga).subscribe_on(NewThreadScheduler()).to_blocking():
            total_costs.append(result.cost),
            islands_costs.append(sum([island.driver.cost for island in imga.islands]))

        self.assertListEqual(total_costs, islands_costs)
