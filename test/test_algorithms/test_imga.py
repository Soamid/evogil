import unittest

from simulation.run_parallel import prepare


class ImgaTest(unittest.TestCase):

    def test_imga(self):
        internal_driver, _ = prepare("NSGAII", "ZDT1")
        final_driver, problem_mod = prepare("IMGA", "ZDT1", internal_driver)
        print(final_driver())

        imga = final_driver()

        results = []
        imga.steps().subscribe(lambda proxy: results.append(proxy))

        STEPS = 3
        for i in range(STEPS):
            imga.step()

        self.assertEqual(len(results), STEPS)

