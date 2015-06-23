# base
import pathlib
import json

# self
from evotools.config import metric_names
from evotools.serialization import RunResult


def analyse_results(*args, **kwargs):
    for problem_name, problem_mod, algorithms in RunResult.each_result():
        for algo_name, budgets in algorithms:
            for result in budgets:
                print(
                    "{:9} {:14} {:>4} {:>2}".format(problem_name, algo_name, result["budget"], len(result["results"]))
                )
