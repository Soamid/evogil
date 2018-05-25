import unittest

from rx import Observable

from algorithms.base.drivergen import Driver


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
                    driver.step()
                self.assertEqual(driver.step_no, step_no)
