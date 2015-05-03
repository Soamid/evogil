# base
import pathlib
import json

# self
from evotools.config import metric_names


def iterate_results():
    root = pathlib.Path('jsoned')
    for d_problem in [p_problem
                      for p_problem in root.iterdir()
                      if p_problem.is_dir()]:
        sd_problem = False
        for d_algorithm in [p_algo
                            for p_algo in d_problem.iterdir()
                            if p_algo.is_dir()]:
            sd_algorithm = False
            for d_testname in [p_testname
                               for p_testname in d_algorithm.iterdir()
                               if p_testname.is_dir()]:
                sd_testname = False
                for d_budget in sorted([p_budget
                                        for p_budget in d_testname.iterdir()
                                        if p_budget.is_dir()],
                                       key=lambda x: int(x.name)):
                    sd_budget = False


                    results = {}
                    for metrics_name_long, metrics_name in metric_names:
                        data = []
                        cost = []
                        for result_file in d_budget.glob(metrics_name_long + "*.json"):
                            with result_file.open(mode="r") as fh:
                                test_results = json.load(fh)
                                data.append(test_results["metrics"])
                                cost.append(test_results["cost"])
                                results[metrics_name_long] = (data, cost)

                        yield { 'd_problem':    d_problem,
                                'sd_problem':   sd_problem,

                                'd_algorithm':  d_algorithm,
                                'sd_algorithm': sd_algorithm,

                                'd_testname':   d_testname,
                                'sd_testname':  sd_testname,

                                'd_budget':     d_budget,
                                'sd_budget':    sd_budget,

                                'data':         data,
                                'cost':         cost,

                                'metrics_name_long': metrics_name_long,
                                'metrics_name':      metrics_name
                              }

                        sd_problem = True
                        sd_algorithm = True
                        sd_testname = True
                        sd_budget = True
