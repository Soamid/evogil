from contextlib import suppress
from datetime import datetime
import json
from pathlib import Path
import random
import re
from evotools.log_helper import get_logger

logger = get_logger(__name__)


def get_current_time():
    return datetime.today().strftime("%Y-%m-%d.%H%M%S.%f")


class Result:
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
                res = Result(algo, problem,
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

        self.budgets[budget] = population

    def load(self, budget):
        if budget in self.budgets:
            return self.budgets[budget]

        store_path = self.path / "{budget}.json".format(**locals())
        population = self._load_file(store_path)
        return self.budgets.setdefault(budget, population)

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
                    self.budgets[budget] = population
                except (AttributeError, IsADirectoryError, KeyError):
                    pass

    def each_result(self):
        for budget in sorted(self.budgets):
            population = self.budgets[budget]
            yield (budget, population)