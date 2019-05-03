import os
import tempfile
import time
import unittest

from algorithms.base.driver import Driver
from simulation import factory
from simulation.model import SimulationCase
from simulation.worker import TimeWorker



class TimeBoundWorkerTest(unittest.TestCase):

    @unittest.skip("endless loop, solution not ready yet")
    def test_step_number_updated(self):

        class DummyDriver(Driver):

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.counter = 1

            def finish(self):
                return [self.counter]

            def step(self):
                time.sleep(1)
                self.counter += 1
                print(f"new counter {self.counter}")

        class DummyProblem:
            @property
            def fitnesses(self):
                return lambda x: 2 * x

        with (tempfile.TemporaryDirectory(prefix="evogil_time_bound_")) as temp_dir:

            simulation_case = SimulationCase(
                "test_problem",
                "test_algo",
                0,
                None,
                temp_dir,
                timeout=10,
                sampling_interval=2,
            )

            factory.prepare = lambda algo_name, problem_mod: (DummyDriver, DummyProblem())

            time_runner = TimeWorker(simulation_case, 0)
            time_runner.run()

            print(os.listdir(temp_dir))
