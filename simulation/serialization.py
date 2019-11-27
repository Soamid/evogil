import re
from collections import defaultdict
from contextlib import suppress
from importlib import import_module
from pathlib import Path

from simulation import model, metrics_processor
from simulation.model import SimulationCase
from simulation.serializer import Serializer, ResultWithMetadata

RESULTS_DIR = "../results_temp/results_k2"


class ResultsExtractor:
    def load(self, algo_name, problem_name, results_path):
        runs = self._each_run(algo_name, problem_name, results_path)
        return self.load_result(runs)

    def load_result(self, runs):
        raise NotImplementedError

    def _each_run(self, algo, problem, results_path="results"):
        rootpath = Path(results_path, problem, algo)
        run_no = 0
        for candidate in sorted(rootpath.iterdir()):
            try:
                match = re.fullmatch(
                    "(?P<rundate>\d{4}-\d{2}-\d{2}\.\d{2}\d{2}\d{2}\.\d{6})__(?P<runid>\d{7})",
                    candidate.name,
                )
                matchdict = match.groupdict()
                run_id = matchdict["runid"]
                run_date = matchdict["rundate"]
                simulation_case = SimulationCase(
                    problem,
                    algo,
                    run_id,
                    None,
                    results_path,
                    model.get_simulation_id(run_id, run_date),
                )
                yield (simulation_case, run_no)
                run_no += 1
            except AttributeError:
                pass


class NumberMeasuredResultExtractor(ResultsExtractor):
    def __init__(self, property_name):
        self.property_name = property_name

    def load_result(self, runs):
        by_number = defaultdict(list)
        for simulation_case, run_no in runs:
            for runbudget in self.load_number_measured_results(simulation_case, run_no):
                by_number[int(runbudget.name)].append(runbudget)
        return [
            (by_number[number], {self.property_name: number})
            for number in sorted(by_number)
        ]

    def load_number_measured_results(self, simulation_case, run_no):
        numbers = []
        serializer = Serializer(simulation_case)
        with suppress(FileNotFoundError):
            for candidate in sorted(serializer.path.iterdir()):
                try:
                    match = re.fullmatch(f"(?P<{self.property_name}>[0-9]+)\.pickle", candidate.name)

                    number = int(match.groupdict()[self.property_name])
                    population_pickle = serializer.load(number)

                    res = ResultWithMetadata(
                        population_pickle, candidate, run_no, simulation_case
                    )
                    numbers.append(res)
                except (AttributeError, IsADirectoryError):
                    pass
        return numbers


class BudgetResultsExtractor(NumberMeasuredResultExtractor):
    def __init__(self):
        super().__init__("budget")


class TimeResultsExtractor(NumberMeasuredResultExtractor):
    def __init__(self):
        super().__init__("time")


def each_result(result_extractor: ResultsExtractor, results_path=RESULTS_DIR):
    def f_algo(problem_path, algo_path, problem_mod):
        algo_name = algo_path.name
        problem_name = problem_path.name
        for results, config in result_extractor.load(
            algo_name, problem_name, results_path
        ):
            yield {
                "problem": problem_name,
                "algo": algo_name,
                "results": results,
                "analysis": metrics_processor.yield_metrics(results, problem_mod),
                **config,
            }

    def f_problem(problem_path, problem_mod):
        for algo_path in problem_path.iterdir():
            if algo_path.is_dir():
                yield algo_path.name, f_algo(problem_path, algo_path, problem_mod)

    with suppress(FileNotFoundError):
        for problem in Path(results_path).iterdir():
            problem_mod = ".".join(["problems", problem.name, "problem"])
            problem_mod = import_module(problem_mod)
            yield problem.name, problem_mod, f_problem(problem, problem_mod)
