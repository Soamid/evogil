import glob
import os
import sys
import tempfile
import unittest
from pathlib import Path

import rx.operators as ops
from rx.concurrency import NewThreadScheduler

from algorithms.base.driver import StepsRun
from algorithms.base.model import ProgressMessage
from simulation import run_config, serialization
from simulation.factory import prepare


class DriverTest(unittest.TestCase):
    def test_create_and_run_all_supported_algorithms(self):
        test_cases = run_config.algorithms
        for test_case in test_cases:
            with self.subTest(algorithm=test_case):
                algo_factory, _ = prepare(test_case, "ZDT1")
                algorithm = algo_factory()

                simple_simulation = StepsRun(1)
                result = list(
                    simple_simulation.create_job(algorithm)
                    .pipe(ops.subscribe_on(NewThreadScheduler()), ops.to_iterable())
                    .run()
                )
                self.assertEqual(1, len(result))
                self.assertIsInstance(result[0], ProgressMessage)

    def test_smoke(self):
        with (tempfile.TemporaryDirectory(prefix="evogil_smoke_")) as temp_dir:
            python = sys.executable
            os.system(f"{python} evogil.py run 50,100 -a NSGAII -p zdt1 -d {temp_dir}")

            results = list(glob.glob(f"{temp_dir}/ZDT1/NSGAII/*/*.pickle"))
            self.assertTrue(results)
            for result_file in results:
                print("Found result file: " + result_file)
                loaded_result = serialization.RunResult.load_file(Path(result_file))
                self.assertIsNotNone(loaded_result)
