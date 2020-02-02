import unittest

from algorithms.base.driver import Driver, ProgressMessage
from simulation.factory import prepare


class DriverTest(unittest.TestCase):
    def test_step_number_updated(self):
        steps = [0, 1, 2]

        class DummyDriver(Driver):
            def step(self):
                pass

        for step_no in steps:
            with self.subTest():
                driver = DummyDriver()
                for _ in range(step_no):
                    driver.next_step()
                self.assertEqual(driver.step_no, step_no)

    def test_default_proxy_is_progress_proxy(self):
        driver_factory, _ = prepare("NSGAII", "ZDT1")
        driver = driver_factory()

        for _ in range(3):
            with self.subTest():
                proxy = driver.next_step()
                self.assertIsInstance(proxy, ProgressMessage)
                self.assertEqual(proxy.step_no, driver.step_no - 1)
                self.assertEqual(proxy.cost, driver.cost)
