# base

# self
from simulation import serialization
from simulation.serialization import BudgetResultsExtractor


def analyse_results(*args, **kwargs):
    for problem_name, problem_mod, algorithms in serialization.each_result(
        BudgetResultsExtractor()
    ):
        for algo_name, budgets in algorithms:
            for result in budgets:
                print(
                    "{:9} {:14} {:>4} {:>2}".format(
                        problem_name,
                        algo_name,
                        result["budget"],
                        len(result["results"]),
                    )
                )
