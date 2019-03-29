import fnmatch
import logging
import os
import pickle
import random
import re
from collections import defaultdict
from contextlib import suppress
from datetime import datetime
from functools import partial
from importlib import import_module
from itertools import chain
from pathlib import Path

from metrics import metrics
from simulation import factory
from simulation.factory import SimulationCase
from simulation.serializer import Serializer, Result

RESULTS_DIR = '../results_temp/results_k2'


class RunResult:

    def __init__(self, simulation_case: SimulationCase):
        self.serializer = Serializer(simulation_case)
        self.simulation_case = simulation_case
        self.budgets = {}

    @staticmethod
    def get_bounds():
        """ Wylicza górne granice wymiarów przeciwdziedziny dla wyznaczonych problemów """
        for problem_name, problem_mod, algorithms in RunResult.each_result():
            all_results = chain.from_iterable(run.fitnesses
                                              for algo_name, budgets in algorithms
                                              for result in budgets
                                              for run in result["results"])
            res = [max(*l) for l in zip(*all_results)]

            # print(problem_name, res)

    @staticmethod
    def each_run(algo, problem, results_path='results'):
        rootpath = Path(results_path,
                        problem,
                        algo)
        run_no = 0
        for candidate in sorted(rootpath.iterdir()):
            try:
                match = re.fullmatch("(?P<rundate>\d{4}-\d{2}-\d{2}\.\d{2}\d{2}\d{2}\.\d{6})__(?P<runid>\d{7})",
                                     candidate.name)
                matchdict = match.groupdict()
                run_id = matchdict["runid"]
                run_date = matchdict["rundate"]
                simulation_case = SimulationCase(problem, algo, None, run_id, None, results_path,
                                                 factory.get_simulation_id(run_id, run_date))
                res = RunResult(simulation_case)
                res.preload_all_budgets(run_no)
                run_no += 1
                yield res
            except AttributeError:
                pass

    @staticmethod
    def each_result(results_path=RESULTS_DIR):
        cache = defaultdict(list)

        def f_metrics(result_list, problem_mod):
            """ Pierwszy *zawsze* będzie cost. To ważne.
            Nazwa `igd` nie może się zmieniać, to ważne dla `best_fronts`.
            @type result_list : list[RunResult.RunResultBudget]
            """
            yield "cost", "cost", [partial(float, x.cost) for x in result_list]
            yield "gd", "generational distance", [partial(x.generational_distance, pareto=problem_mod.pareto_front)
                                                  for x in result_list]
            yield "igd", "inverse generational distance", [
                partial(x.inverse_generational_distance, pareto=problem_mod.pareto_front)
                for x in result_list]
            yield "ahd", "average hausdorff distance", [
                partial(x.average_hausdorff_distance, pareto=problem_mod.pareto_front) for x in result_list]
            yield "epsilon", "epsilon", [partial(x.epsilon, pareto=problem_mod.pareto_front)
                                         for x in result_list]
            yield "extent", "extent", [partial(x.extent, pareto=problem_mod.pareto_front)
                                       for x in result_list]
            yield "spacing", "spacing", [partial(x.spacing, pareto=problem_mod.pareto_front)
                                         for x in result_list]
            yield "ndr", "non domination ratio", [partial(x.non_domination_ratio, pareto=problem_mod.pareto_front)
                                                  for x in result_list]
            yield "hypervolume", "hypervolume", [partial(x.hypervolume, pareto=problem_mod.pareto_front)
                                                 for x in result_list]
            yield "pdi", "pareto dominance indicator", [
                partial(x.pareto_dominance_indicator, cache=cache)
                for x in result_list]

        def f_algo(problem_path, algo_path, problem_mod):
            by_budget = defaultdict(list)
            for run in RunResult.each_run(algo_path.name, problem_path.name, results_path):
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
                if algo_path.is_dir():
                    yield algo_path.name, f_algo(problem_path, algo_path, problem_mod)

        with suppress(FileNotFoundError):
            for problem in Path(results_path).iterdir():
                problem_mod = '.'.join(['problems', problem.name, 'problem'])
                problem_mod = import_module(problem_mod)
                yield problem.name, problem_mod, f_problem(problem, problem_mod)

    def store(self, budget, cost, population, population_fitnesses):
        store_path = self.serializer.store(Result(population, population_fitnesses, cost=cost), str(budget))
        self.budgets[budget] = RunResultBudget(self.simulation_case.problem_name,
                                               self.simulation_case.algorithm_name,
                                               budget,
                                               None,
                                               cost,
                                               population,
                                               population_fitnesses,
                                               store_path)

    def load(self, budget):
        if budget in self.budgets:
            return self.budgets[budget]

        result = self.serializer.load(str(budget))

        res = RunResultBudget(self.simulation_case.problem_name,
                              self.simulation_case.algorithm_name,
                              budget,
                              None,
                              result.additional_data["cost"],
                              result.population,
                              result.fitnesses,
                              result.store_path)
        return self.budgets.setdefault(budget, res)

    @staticmethod
    def load_file(path):
        with path.open(mode='rb') as fh:
            return pickle.load(fh)

    @staticmethod
    def save_file(path, obj):
        with path.open(mode='wb') as fh:
            pickle.dump(obj, fh)

    def preload_all_budgets(self, run_no):
        self.budgets = {}
        with suppress(FileNotFoundError):
            for candidate in sorted(self.serializer.path.iterdir()):
                try:
                    match = re.fullmatch("(?P<budget>[0-9]+)\.pickle",
                                         candidate.name)

                    budget = int(match.groupdict()["budget"])
                    population_pickle = self.serializer.load(budget)

                    res = RunResultBudget(self.simulation_case.problem_name,
                                          self.simulation_case.algorithm_name,
                                          budget,
                                          run_no,
                                          population_pickle.additional_data["cost"],
                                          population_pickle.population,
                                          population_pickle.fitnesses,
                                          candidate)

                    self.budgets[budget] = res
                except (AttributeError, IsADirectoryError):
                    pass

    def each_budget(self):
        for budget in sorted(self.budgets):
            yield self.budgets[budget]


class RunResultBudget:
    def __init__(self, problem, algo, budget, run_no, cost, population, fitnesses, path):
        self.problem = problem
        self.algo = algo
        self.budget = budget
        self.run_no = run_no
        self.cost = cost
        self.population = population
        self.fitnesses = fitnesses
        self.non_dominated_fitnesses = metrics.filter_not_dominated(fitnesses)
        self.path = path
        self.metrics = {}

    def _get_metric(self, metric_name, metric_mod_name=None, metric_params=None):
        logger = logging.getLogger(__name__)
        try:
            if not metric_mod_name:
                metric_mod_name = ["metrics", "metrics"]
            if not metric_params:
                metric_params = {}

            if metric_name in self.metrics:
                return self.metrics[metric_name]

            metric_path = self.path.parent / "{self.budget}.{metric_name}.pickle".format(**locals())

            with suppress(FileNotFoundError):
                with metric_path.open(mode='rb') as fh:
                    res = pickle.load(fh)
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
            metric_val = metric_fun(self.fitnesses, self.non_dominated_fitnesses, **metric_params)

            with metric_path.open(mode='wb') as fh:
                pickle_store = {"value": metric_val,
                                "metric": {
                                    "name": metric_name,
                                    "module": metric_mod_name,
                                    "params": metric_params}
                                }
                pickle.dump(pickle_store, fh)

            return self.metrics.setdefault(metric_name, metric_val)
        except Exception as e:
            logger.exception("Error: RunResultBudget.budget=%d .cost=%d .path=%s -> metric=%s",
                             self.budget, self.cost, self.path, metric_name,
                             exc_info=e)
            raise e

    def generational_distance(self, pareto):
        return self._get_metric("generational_distance",
                                metric_params={"pareto": pareto})

    def inverse_generational_distance(self, pareto):
        return self._get_metric("inverse_generational_distance",
                                metric_params={"pareto": pareto})

    def average_hausdorff_distance(self, pareto):
        return self._get_metric("average_hausdorff_distance", metric_params={"pareto": pareto})

    def epsilon(self, pareto):
        return self._get_metric("epsilon",
                                metric_params={"pareto": pareto})

    def extent(self, pareto):
        return self._get_metric("extent",
                                metric_params={"pareto": pareto})

    def spacing(self, pareto):
        return self._get_metric("spacing",
                                metric_params={"pareto": pareto})

    def non_domination_ratio(self, pareto):
        return self._get_metric("non_domination_ratio",
                                metric_params={"pareto": pareto})

    def hypervolume(self, pareto):
        return self._get_metric("hypervolume",
                                metric_params={"pareto": pareto})

    def pareto_dominance_indicator(self, cache):
        if (self.problem, self.budget, self.run_no) not in cache:
            self.preload_results_for_problem(cache)
        try:
            all_solutions = cache[(self.problem, self.budget, self.run_no)]
            return self._get_metric("pareto_dominance_indicator", metric_params={"all_solutions": all_solutions})

        except KeyError:
            logger = logging.getLogger(__name__)
            logger.exception(
                "No matching run for: problem={} algo={} run_no{}={}".format(self.problem, self.budget, self.run_no))
            return None

    def preload_results_for_problem(self, cache):
        problem_path = self.path.parent.parent.parent
        print("Loading for problem : {}".format(problem_path.name))
        for algo_path in problem_path.iterdir():
            if algo_path.is_dir():
                runs = [run for run in algo_path.iterdir() if run.is_dir()]
                for i in range(len(runs)):
                    # print(runs[i].name)
                    for result_file in runs[i].iterdir():
                        try:
                            match = re.fullmatch("(?P<budget>[0-9]+)\.pickle",
                                                 result_file.name)

                            budget = int(match.groupdict()["budget"])
                            result = RunResult.load_file(result_file)

                            print("Caching for algo: {} ... {}".format(algo_path.name, (self.problem, budget, i)))
                            cache[(self.problem, budget, i)].append(result.fitnesses)
                        except (AttributeError, IsADirectoryError):
                            pass
        self.filter_non_dominated_in_cache(cache)

    def filter_non_dominated_in_cache(self, cache):
        problem_keys = sorted(filter(lambda run_key: run_key[0] == self.problem, cache))
        problem_solutions = [cache[key] for key in problem_keys]

        problem_path = self.path.parent.parent.parent
        # cache_path = problem_path / problem_hash

        problem_cache_file = problem_path / "{}_nondominated".format(self.problem)
        try:
            solutions, problem_nondominated = RunResult.load_file(problem_cache_file)
        except IOError:
            problem_nondominated = {}
            solutions = None

        if solutions and solutions == problem_solutions:
            pass
            print("Cache for problem {} does not changed, loading nondominated solutions from file...")
        else:
            print("Cache for problem {} changed, calculating new nondominated... ")
            self.clear_old_pdi_metrics()
            for key in problem_keys:
                print('Filtering non dominated for: ' + str(key))
                solutions = cache[key]
                problem_nondominated[key] = set(metrics.filter_not_dominated(tuple(y) for s in solutions for y in s))

            RunResult.save_file(problem_cache_file, (problem_solutions, problem_nondominated))

        cache.update(problem_nondominated)
        print("Cache of results -> cache of nondominated results")

    def clear_old_pdi_metrics(self):
        problem_path = self.path.parent.parent.parent

        for filename in fnmatch.filter([str(p) for p in problem_path.iterdir()], "*{}_*".format(self.problem)):
            os.remove(filename)
            print("Removing file: " + filename)

        for root, dirnames, filenames in os.walk(str(problem_path)):
            for filename in fnmatch.filter(filenames, '*.pareto_dominance_indicator.pickle'):
                file_path = os.path.join(root, filename)
                print("Removing file: " + str(file_path))
                os.remove(file_path)
