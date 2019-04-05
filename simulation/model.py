import random
from datetime import datetime
from typing import List


def get_simulation_id(run_id, run_date=None):
    run_date = run_date if run_date else datetime.today().strftime("%Y-%m-%d.%H%M%S.%f")
    if not run_id:
        run_id = random.randint(1000000, 9999999)
    return f"{run_date}__{run_id:0>7}"


class SimulationCase:
    def __init__(self, problem_name: str, algorithm_name: str, budgets: List[int], run_id: int, renice: str,
                 results_dir: str, id=None):
        self.problem_name = problem_name
        self.algorithm_name = algorithm_name
        self.budgets = budgets
        self.run_id = run_id
        self.renice = renice
        self.results_dir = results_dir
        self.id = id if id else get_simulation_id(run_id)

    @property
    def config(self):
        return self.problem_name, self.algorithm_name

    def __repr__(self):
        return str(self)

    def __str__(self):
        return 'Simulation:' + str(vars(self))
