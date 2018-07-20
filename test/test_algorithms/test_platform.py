import unittest

from rx.concurrency import NewThreadScheduler

from algorithms.base.drivergen import StepsRun
from algorithms.base.model import ProgressMessage
from simulation import run_config
from simulation.factory import prepare


class DriverTest(unittest.TestCase):

    def test_create_and_run_all_supported_algorithms(self):
        test_cases = run_config.algorithms
        for test_case in test_cases:
            with self.subTest(algorithm=test_case):
                algo_factory, _ = prepare(test_case, "ZDT1")
                algorithm = algo_factory()

                simple_simulation = StepsRun(1)
                result = list(simple_simulation.create_job(algorithm).subscribe_on(NewThreadScheduler()).to_blocking())
                self.assertEqual(1, len(result))
                self.assertIsInstance(result[0], ProgressMessage)