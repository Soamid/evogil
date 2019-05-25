import fnmatch
import logging
import os
import pickle
import re
from collections import defaultdict
from contextlib import suppress
from functools import partial
from importlib import import_module
from pathlib import Path
from typing import List

from metrics import metrics
from simulation import serializer
from simulation.serializer import ResultWithMetadata


def yield_metrics(result_list: List[ResultWithMetadata], problem_mod):
    for result in result_list:
        result.non_dominated_fitnesses = metrics.filter_not_dominated(result.fitnesses)

    yield "cost", "cost", [
        partial(float, x.additional_data["cost"]) for x in result_list
    ]
    yield "gd", "generational distance", [
        partial(generational_distance, result=result, pareto=problem_mod.pareto_front)
        for result in result_list
    ]
    yield "igd", "inverse generational distance", [
        partial(
            inverse_generational_distance,
            result=result,
            pareto=problem_mod.pareto_front,
        )
        for result in result_list
    ]
    yield "ahd", "average hausdorff distance", [
        partial(
            average_hausdorff_distance, result=result, pareto=problem_mod.pareto_front
        )
        for result in result_list
    ]
    yield "epsilon", "epsilon", [
        partial(epsilon, result=result, pareto=problem_mod.pareto_front)
        for result in result_list
    ]
    yield "extent", "extent", [
        partial(extent, result=result, pareto=problem_mod.pareto_front)
        for result in result_list
    ]
    yield "spacing", "spacing", [
        partial(spacing, result=result, pareto=problem_mod.pareto_front)
        for result in result_list
    ]
    yield "ndr", "non domination ratio", [
        partial(non_domination_ratio, result=result, pareto=problem_mod.pareto_front)
        for result in result_list
    ]
    yield "hypervolume", "hypervolume", [
        partial(hypervolume, result=result, pareto=problem_mod.pareto_front)
        for result in result_list
    ]
    cache = defaultdict(list)
    yield "pdi", "pareto dominance indicator", [
        partial(pareto_dominance_indicator, result=result, cache=cache)
        for result in result_list
    ]


def get_metric(
    result: ResultWithMetadata, metric_name, metric_mod_name=None, metric_params=None
):
    logger = logging.getLogger(__name__)
    try:
        if not metric_mod_name:
            metric_mod_name = ["metrics", "metrics"]
        if not metric_params:
            metric_params = {}

        metric_path = result.path.parent / f"{result.name}.{metric_name}.pickle"

        with suppress(FileNotFoundError):
            with metric_path.open(mode="rb") as fh:
                res = pickle.load(fh)
                metric_val = res["value"]
                if res["metric"]["params"] != metric_params:
                    e = Exception(
                        "You have changed params of the metric. "
                        "recalculating / per-param storage not implemented"
                    )
                    logger.exception(
                        "Metric params do not match: %s != %s",
                        res["metric"]["params"],
                        metric_params,
                        exc_info=e,
                    )
                    raise e
            return metric_val

        # noinspection PyUnreachableCode
        metric_mod = import_module(".".join(metric_mod_name))
        metric_fun = getattr(metric_mod, metric_name)
        metric_val = metric_fun(
            result.fitnesses, result.non_dominated_fitnesses, **metric_params
        )

        with metric_path.open(mode="wb") as fh:
            pickle_store = {
                "value": metric_val,
                "metric": {
                    "name": metric_name,
                    "module": metric_mod_name,
                    "params": metric_params,
                },
            }
            pickle.dump(pickle_store, fh)

        return metric_val
    except Exception as e:
        logger.exception(
            "Error: Result.path=%s -> metric=%s", result.path, metric_name, exc_info=e
        )
        raise e


def generational_distance(result: ResultWithMetadata, pareto):
    return get_metric(result, "generational_distance", metric_params={"pareto": pareto})


def inverse_generational_distance(result: ResultWithMetadata, pareto):
    return get_metric(
        result, "inverse_generational_distance", metric_params={"pareto": pareto}
    )


def average_hausdorff_distance(result: ResultWithMetadata, pareto):
    return get_metric(
        result, "average_hausdorff_distance", metric_params={"pareto": pareto}
    )


def epsilon(result: ResultWithMetadata, pareto):
    return get_metric(result, "epsilon", metric_params={"pareto": pareto})


def extent(result: ResultWithMetadata, pareto):
    return get_metric(result, "extent", metric_params={"pareto": pareto})


def spacing(result: ResultWithMetadata, pareto):
    return get_metric(result, "spacing", metric_params={"pareto": pareto})


def non_domination_ratio(result: ResultWithMetadata, pareto):
    return get_metric(result, "non_domination_ratio", metric_params={"pareto": pareto})


def hypervolume(result: ResultWithMetadata, pareto):
    return get_metric(result, "hypervolume", metric_params={"pareto": pareto})


def pareto_dominance_indicator(result: ResultWithMetadata, cache):
    problem = result.simulation_case.problem_name
    algorithm = result.simulation_case.algorithm_name
    run_no = result.run_no
    if (problem, result.name, run_no) not in cache:
        preload_results_for_problem(cache, result.path.parent.parent.parent)
    try:
        all_solutions = cache[(problem, result.name, run_no)]
        print("cache: " +str(cache))
        return get_metric(
            result,
            "pareto_dominance_indicator",
            metric_params={"all_solutions": all_solutions},
        )

    except KeyError:
        logger = logging.getLogger(__name__)
        logger.exception(
            "No matching run for: problem=%s algo=%s run_no=%s",
            problem,
            algorithm,
            run_no,
        )
        return None


def preload_results_for_problem(cache, problem_path: Path):
    logger = logging.getLogger(__name__)
    problem_name = problem_path.name
    logger.debug("Loading for problem : {}".format(problem_name))
    for algo_path in problem_path.iterdir():
        if algo_path.is_dir():
            runs = [run for run in algo_path.iterdir() if run.is_dir()]
            for run_no in range(len(runs)):
                for result_file in runs[run_no].iterdir():
                    try:
                        print(result_file)
                        match = re.fullmatch(
                            "(?P<name>[0-9]+)\.pickle", result_file.name
                        )

                        result_name = match.groupdict()["name"]
                        result = serializer.load_file(result_file)

                        logger.debug(
                            "Caching for algo: {} ... {}".format(
                                algo_path.name, (problem_name, result_name, run_no)
                            )
                        )
                        cache[(problem_name, result_name, run_no)].append(
                            result.fitnesses
                        )
                    except (AttributeError, IsADirectoryError):
                        pass
    filter_non_dominated_in_cache(problem_path, cache)


def filter_non_dominated_in_cache(problem_path: Path, cache):
    logger = logging.getLogger(__name__)
    problem_name = problem_path.name
    problem_keys = sorted(filter(lambda run_key: run_key[0] == problem_name, cache))
    problem_solutions = [cache[key] for key in problem_keys]

    problem_cache_file = problem_path / f"{problem_name}_nondominated"
    try:
        solutions, problem_nondominated = serializer.load_file(problem_cache_file)
    except IOError:
        problem_nondominated = {}
        solutions = None

    if solutions and solutions == problem_solutions:
        pass
        logger.debug(
            "Cache for problem {} does not changed, loading nondominated solutions from file..."
        )
    else:
        logger.debug("Cache for problem {} changed, calculating new nondominated... ")
        clear_old_pdi_metrics(problem_path)
        for key in problem_keys:
            logger.debug("Filtering non dominated for: " + str(key))
            solutions = cache[key]
            problem_nondominated[key] = set(
                metrics.filter_not_dominated(tuple(y) for s in solutions for y in s)
            )

        serializer.save_file(
            problem_cache_file, (problem_solutions, problem_nondominated)
        )

    cache.update(problem_nondominated)
    print("Cache of results -> cache of nondominated results")


def clear_old_pdi_metrics(problem_path: Path):
    logger = logging.getLogger(__name__)

    for filename in fnmatch.filter(
        [str(p) for p in problem_path.iterdir()], "*{}_*".format(problem_path.name)
    ):
        os.remove(filename)
        logger.debug("Removing file: " + filename)

    for root, dirnames, filenames in os.walk(str(problem_path)):
        for filename in fnmatch.filter(
            filenames, "*.pareto_dominance_indicator.pickle"
        ):
            file_path = os.path.join(root, filename)
            logger.debug("Removing file: " + str(file_path))
            os.remove(file_path)
