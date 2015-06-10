from contextlib import suppress
from datetime import datetime
from importlib import import_module
import json
from pathlib import Path
import random
import re
from evotools.log_helper import get_logger

logger = get_logger(__name__)


class RunResult:
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
                         "{rundate}__{runid}".format(**locals()))
        self.budgets = {}

    def store(self, budget, population):
        with suppress(FileExistsError):
            self.path.mkdir(parents=True)

        store_path = self.path / "{budget}.json".format(**locals())
        with store_path.open(mode='w') as fh:
            json.dump({"population": population}, fh)

        self.budgets[budget] = RunResult.RunResultBudget(budget, population, store_path)

    def load(self, budget):
        if budget in self.budgets:
            return self.budgets[budget]

        store_path = self.path / "{budget}.json".format(**locals())
        population = self._load_file(store_path)
        res = RunResult.RunResultBudget(budget, population, store_path)
        return self.budgets.setdefault(budget, res)

    @staticmethod
    def _load_file(path):
        with path.open(mode='r') as fh:
            population_json = json.load(fh)
            return population_json["population"]

    def preload_all_budgets(self):
        self.budgets = {}
        with suppress(FileNotFoundError):
            for candidate in sorted(self.path.iterdir()):
                try:
                    match = re.fullmatch("(?P<budget>[0-9]+)\.json",
                                         candidate.name)
                    budget = int(match.groupdict()["budget"])
                    population = self._load_file(candidate)
                    res = RunResult.RunResultBudget(budget, population, candidate)
                    self.budgets[budget] = res
                except (AttributeError, IsADirectoryError, KeyError):
                    pass

    class RunResultBudget:
        def __init__(self, budget, population, path):
            self.budget = budget
            self.population = population
            self.path = path
            self.metrics = {}

        def _get_metric(self, metric_name, metric_mod=None, metric_params=None):
            if metric_name in self.metrics:
                return self.metrics[metric_name]

            metric_path = self.path.parent / "{self.budget}.{metric_name}.json".format(**locals())

            try:
                with metric_path.open(mode='r') as fh:
                    res = json.load(fh)
                    metric_val = res["value"]
                self.metrics[metric_name] = metric_val
                return metric_val
            except FileNotFoundError:
                pass

            if not metric_mod:
                metric_mod = ["evotools", "metrics"]
            if not metric_params:
                metric_params = {}
            metric_mod = import_module('.'.join(metric_mod))
            metric_fun = getattr(metric_mod, metric_name)

            metric_val = metric_fun(self.population, **metric_params)
            return self.metrics.setdefault(metric_name, metric_val)

        def distance_from_pareto(self, pareto):
            return self._get_metric("distance_from_pareto", metric_params={"pareto": pareto})

        def distribution(self):
            return self._get_metric("distribution", metric_params={"sigma": 0.5})

        def extent(self):
            return self._get_metric("extent")

    def each_result(self):
        for budget in sorted(self.budgets):
            res = self.budgets[budget]
            yield res