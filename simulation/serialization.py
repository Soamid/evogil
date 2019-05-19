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
                run_no += 1
                yield (simulation_case, run_no)
            except AttributeError:
                pass


class BudgetResultsExtractor(ResultsExtractor):
    def load_result(self, runs):
        by_budget = defaultdict(list)
        for simulation_case, run_no in runs:
            for runbudget in self.load_budget_results(simulation_case, run_no):
                by_budget[int(runbudget.name)].append(runbudget)
        return [(by_budget[budget], {"budget": budget}) for budget in sorted(by_budget)]

    def load_budget_results(self, simulation_case, run_no):
        budgets = []
        serializer = Serializer(simulation_case)
        with suppress(FileNotFoundError):
            for candidate in sorted(serializer.path.iterdir()):
                try:
                    match = re.fullmatch("(?P<budget>[0-9]+)\.pickle", candidate.name)

                    budget = int(match.groupdict()["budget"])
                    population_pickle = serializer.load(budget)

                    res = ResultWithMetadata(
                        population_pickle, candidate, run_no, simulation_case
                    )
                    budgets.append(res)
                except (AttributeError, IsADirectoryError):
                    pass
        return budgets


def each_result(result_extractor: ResultsExtractor, results_path=RESULTS_DIR):
    def f_algo(problem_path, algo_path, problem_mod):
        algo_name = algo_path.name
        problem_name = problem_path.name
        for results, config in result_extractor.load(algo_name, problem_name, results_path):
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

