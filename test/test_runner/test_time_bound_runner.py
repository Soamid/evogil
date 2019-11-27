import os
import tempfile
import time
import unittest

from algorithms.base.driver import Driver
from simulation import factory
from simulation.model import SimulationCase
from simulation.serializer import Serializer, Result
from simulation.worker import TimeWorker
from test.test_common import test_util


class TimeBoundWorkerTest(unittest.TestCase):
    class DummyDriver(Driver):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.counter = 1

        def finalized_population(self):
            return [self.counter]

        def step(self):
            time.sleep(1)
            self.counter += 1
            print(f"new counter {self.counter}")

    class DummyProblem:
        @property
        def fitnesses(self):
            return [lambda x: 2 * x]

    def test_step_number_updated(self):
        # given:
        timeout = 6
        time_interval = 2
        expected_slots = set(range(time_interval, timeout + 1, time_interval))

        with (tempfile.TemporaryDirectory(prefix="evogil_time_bound_")) as temp_dir:
            simulation_case = SimulationCase(
                "test_problem",
                "test_algo",
                0,
                None,
                temp_dir,
                timeout=timeout,
                sampling_interval=time_interval,
            )
            results_path = f"{temp_dir}/test_problem/test_algo/{simulation_case.id}"
            serializer = Serializer(simulation_case)

            factory.prepare = lambda algo_name, problem_mod: (
                self.DummyDriver,
                self.DummyProblem(),
            )

            time_runner = TimeWorker(simulation_case, 0)

            # when
            time_runner.run()

            # then
            result_files = os.listdir(results_path)
            filled_slots = set(int(filename.split(".")[0]) for filename in result_files)

            result_values = []

            print("result files: " + str(result_files))
            print("results: ")
            for slot in filled_slots:
                result = serializer.load(str(slot))
                self.assertIsInstance(result, Result)
                result_values.append(result.population)
                print(f"{slot} : {result.population}")

            self.assertEqual(expected_slots, filled_slots)
            self.assertTrue(test_util.non_decreasing(result_values))
