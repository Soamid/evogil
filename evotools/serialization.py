from collections import defaultdict
from contextlib import suppress
from datetime import datetime
from importlib import import_module
from itertools import chain
import json
import logging
from pathlib import Path
import random
import re



class RunResult:
    @staticmethod
    def get_bounds():
        """ Wylicza górne granice wymiarów przeciwdziedziny dla wyznaczonych problemów """
        for problem_name, algorithms in RunResult.each_result():
            all_results = chain.from_iterable(run.fitnesses
                                              for algo_name, budgets in algorithms
                                              for result in budgets
                                              for run in result["results"])
            res = [max(*l) for l in zip(*all_results)]

            print(problem_name, res)

    @staticmethod
    def each_run(algo, problem):
        rootpath = Path('results',
                        problem,
                        algo)
        for candidate in sorted(rootpath.iterdir()):
            try:
                match = re.fullmatch("(?P<rundate>\d{4}-\d{2}-\d{2}\.\d{2}\d{2}\d{2}\.\d{6})__(?P<runid>\d{7})",
                                     candidate.name)
                matchdict = match.groupdict()
                res = RunResult(algo, problem,
                                rundate=matchdict["rundate"],
                                runid=matchdict["runid"])
                res.preload_all_budgets()
                yield res
            except AttributeError:
                pass

    @staticmethod
    def each_result():
        def f_metrics(result_list, problem_mod):
            """ Pierwszy *zawsze* będzie cost. To ważne.
            @type result_list : list[RunResult.RunResultBudget]
            """
            yield "cost", "cost", [float(x.cost) for x in result_list]
            yield "distrib", "distribution", [x.distribution() for x in result_list]
            yield "extent", "extent", [x.extent() for x in result_list]
            yield "dst", "distance from pareto", [x.distance_from_pareto(pareto=problem_mod.pareto_front) for x in result_list]

        def f_algo(problem_path, algo_path, problem_mod):
            by_budget = defaultdict(list)
            for run in RunResult.each_run(algo_path.name, problem_path.name):
                for runbudget in run.each_budget():
                    by_budget[runbudget.budget].append(runbudget)
            for budget in sorted(by_budget):
                yield {
                    "problem": problem_path.name,
                    "algo": algo_path.name,
                    "budget": budget,
                    "results": by_budget[budget],
                    "analysis": f_metrics(by_budget[budget], problem_mod)
                }

        def f_problem(problem_path, problem_mod):
            for algo_path in problem_path.iterdir():
                yield algo_path.name, f_algo(problem_path, algo_path, problem_mod)

        with suppress(FileNotFoundError):
            for problem in Path('results').iterdir():
                problem_mod = '.'.join(['problems', problem.name, 'problem'])
                problem_mod = import_module(problem_mod)
                yield problem.name, f_problem(problem, problem_mod)

    def __init__(self, algo, problem, rundate=None, runid=None):
        if not rundate:
            rundate = datetime.today().strftime("%Y-%M-%d.%H%M%S.%f")
        if not runid:
            runid = random.randint(1000000, 9999999)
        self.rundate = rundate
        self.runid = runid
        self.path = Path('results',
                         problem,
                         algo,
                         "{rundate}__{runid:0>7}".format(**locals()))
        self.budgets = {}

    def store(self, budget, cost, population, population_fitnesses):
        with suppress(FileExistsError):
            self.path.mkdir(parents=True)

        store_path = self.path / "{budget}.json".format(**locals())
        with store_path.open(mode='w') as fh:
            json_store = {"population": population,
                          "fitnesses": population_fitnesses,
                          "cost": cost}
            json.dump(json_store, fh)

        self.budgets[budget] = RunResult.RunResultBudget(budget,
                                                         cost,
                                                         population,
                                                         population_fitnesses,
                                                         store_path)

    def load(self, budget):
        if budget in self.budgets:
            return self.budgets[budget]

        store_path = self.path / "{budget}.json".format(**locals())
        population_json = self._load_file(store_path)
        res = RunResult.RunResultBudget(budget,
                                        population_json["cost"],
                                        population_json["population"],
                                        population_json["fitnesses"],
                                        store_path)
        return self.budgets.setdefault(budget, res)

    @staticmethod
    def _load_file(path):
        with path.open(mode='r') as fh:
            return json.load(fh)

    def preload_all_budgets(self):
        self.budgets = {}
        with suppress(FileNotFoundError):
            for candidate in sorted(self.path.iterdir()):
                try:
                    match = re.fullmatch("(?P<budget>[0-9]+)\.json",
                                         candidate.name)

                    budget = int(match.groupdict()["budget"])
                    population_json = self._load_file(candidate)

                    res = RunResult.RunResultBudget(budget,
                                                    population_json["cost"],
                                                    population_json["population"],
                                                    population_json["fitnesses"],
                                                    candidate)

                    self.budgets[budget] = res
                except (AttributeError, IsADirectoryError):
                    pass

    def each_budget(self):
        for budget in sorted(self.budgets):
            yield self.budgets[budget]

    class RunResultBudget:
        def __init__(self, budget, cost, population, fitnesses, path):
            self.budget = budget
            self.cost = cost
            self.population = population
            self.fitnesses = fitnesses
            self.path = path
            self.metrics = {}

        def _get_metric(self, metric_name, metric_mod_name=None, metric_params=None):
            logger = logging.getLogger(__name__)
            try:
                if not metric_mod_name:
                    metric_mod_name = ["evotools", "metrics"]
                if not metric_params:
                    metric_params = {}

                if metric_name in self.metrics:
                    return self.metrics[metric_name]

                metric_path = self.path.parent / "{self.budget}.{metric_name}.json".format(**locals())

                with suppress(FileNotFoundError):
                    with metric_path.open(mode='r') as fh:
                        res = json.load(fh)
                        metric_val = res["value"]
                        if res["metric"]["params"] != metric_params:
                            e = Exception("You have changed params of the metric. "
                                          "recalculating / per-param storage not implemented")
                            logger.exception("Metric params do not match: %s != %s",
                                             res["metric"]["params"], metric_params, exc_info=e)
                            raise e
                    self.metrics[metric_name] = metric_val
                    return metric_val

                # noinspection PyUnreachableCode
                metric_mod = import_module('.'.join(metric_mod_name))
                metric_fun = getattr(metric_mod, metric_name)
                metric_val = metric_fun(self.fitnesses, **metric_params)

                with metric_path.open(mode='w') as fh:
                    json_store = {"value": metric_val,
                                  "metric": {
                                      "name": metric_name,
                                      "module": metric_mod_name,
                                      "params": metric_params}
                                  }
                    json.dump(json_store, fh)

                return self.metrics.setdefault(metric_name, metric_val)
            except Exception as e:
                logger.exception("Error: RunResultBudget.budget=%d .cost=%d .path=%s -> metric=%s",
                                 self.budget, self.cost, self.path, metric_name,
                                 exc_info=e)
                raise e

        def distance_from_pareto(self, pareto):
            return self._get_metric("distance_from_pareto", metric_params={"pareto": pareto})

        def distribution(self):
            return self._get_metric("distribution", metric_params={"sigma": 0.5})

        def extent(self):
            return self._get_metric("extent")
