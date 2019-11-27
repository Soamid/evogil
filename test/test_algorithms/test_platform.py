import glob
import itertools
import os
import sys
import tempfile
import unittest
from pathlib import Path

import rx.operators as ops
from rx.scheduler import NewThreadScheduler
from thespian.actors import ActorSystem

from algorithms.base.driver import StepsRun
from algorithms.base.model import ProgressMessage
from simulation import run_config, serializer, log_helper
from simulation.factory import prepare


class DriverTest(unittest.TestCase):

    EXPECTED_METRICS = ["ahd", "gd", "igd", "hypervolume", "pdi", "spacing"]
    EXPECTED_FORMATS = [".eps", ".pdf"]

    def test_create_and_run_all_supported_algorithms(self):
        sys = ActorSystem("multiprocTCPBase", logDefs=log_helper.EVOGIL_LOG_CONFIG)
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
        sys.shutdown()

    def test_smoke(self):
        with (tempfile.TemporaryDirectory(prefix="evogil_smoke_")) as temp_dir:
            python = sys.executable
            os.system(
                f"{python} evogil.py run budget 50,100 -a NSGAII -p zdt1 -d {temp_dir}/results"
            )
            self.check_results(temp_dir)
            self.check_plots_metrics(python, temp_dir)
            self.check_plots_summary(python, temp_dir)
            self.check_plots_fronts(python, temp_dir)
            self.check_plots_violin(python, temp_dir)

    def check_results(self, temp_dir):
        results = list(glob.glob(f"{temp_dir}/results/ZDT1/NSGAII/*/*.pickle"))
        self.assertTrue(results)
        for result_file in results:
            print("Found result file: " + result_file)
            loaded_result = serializer.load_file(Path(result_file))
            self.assertIsNotNone(loaded_result)

    def check_plots_metrics(self, python, temp_dir):
        os.system(
            f"{python} evogil.py pictures -d {temp_dir}/results -o {temp_dir}/plots"
        )
        expected_plots = set(
            "".join(names)
            for names in itertools.product(
                ["figures_metrics_ZDT1_"], self.EXPECTED_METRICS, self.EXPECTED_FORMATS
            )
        )
        expected_plots.add("figures_metrics_legend.pdf")
        expected_plots.add("figures_metrics_legend.eps")
        generated_plots = set(
            [
                Path(plot_file).name
                for plot_file in glob.glob(f"{temp_dir}/plots/metrics/*")
            ]
        )
        self.assertEqual(expected_plots, generated_plots)

    def check_plots_summary(self, python, temp_dir):
        os.system(
            f"{python} evogil.py pictures_summary -d {temp_dir}/results -o {temp_dir}/plots"
        )
        expected_plots = set(
            "".join(names)
            for names in itertools.product(
                ["figures_summary_"], self.EXPECTED_METRICS, self.EXPECTED_FORMATS
            )
        )
        generated_plots = set(
            [
                Path(plot_file).name
                for plot_file in glob.glob(f"{temp_dir}/plots/plots_summary/*")
            ]
        )
        self.assertEqual(expected_plots, generated_plots)

    def check_plots_fronts(self, python, temp_dir):
        os.system(
            f"{python} evogil.py best_fronts -d {temp_dir}/results -o {temp_dir}/plots"
        )
        expected_plots = {"figures_metrics_ZDT1.pdf", "figures_metrics_ZDT1.eps"}
        generated_plots = set(
            [
                Path(plot_file).name
                for plot_file in glob.glob(f"{temp_dir}/plots/fronts/*")
            ]
        )
        self.assertEqual(expected_plots, generated_plots)

    def check_plots_violin(self, python, temp_dir):
        os.system(
            f"{python} evogil.py violin -d {temp_dir}/results -o {temp_dir}/plots"
        )
        expected_plots = set(
            "".join(names)
            for names in itertools.product(
                ["figures_violin_ZDT1_"], self.EXPECTED_METRICS, self.EXPECTED_FORMATS
            )
        )
        generated_plots = set(
            [
                Path(plot_file).name
                for plot_file in glob.glob(f"{temp_dir}/plots/plots_violin/*")
            ]
        )
        self.assertEqual(expected_plots, generated_plots)
