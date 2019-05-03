import logging
from contextlib import suppress
from functools import partial
from importlib import import_module
from itertools import product
from typing import List, Dict, Any

from evotools.ea_utils import gen_population
from evotools.random_tools import show_partial, show_conf
from simulation import run_config, serialization
from simulation.model import SimulationCase
from simulation.run_config import NotViableConfiguration

logger = logging.getLogger(__name__)

BUDGETS_PARAM = "budgets"

TIMEOUT_PARAM = "timeout"

SAMPLING_INTERVAL_PARAM = "sampling_interval"


def create_budget_simulation(args: Dict[str, str]):
    params = {BUDGETS_PARAM: parse_budgets(args)}
    return create_simulation(args, params)


def create_time_bound_simulation(args: Dict[str, str]):
    return None  # TODO runner support


def create_simulation(args: Dict[str, str], params: Dict[str, Any]):
    budgets = parse_budgets(args)
    logger.debug("Budgets: %s", budgets)

    order = list(product(run_config.problems, run_config.algorithms))

    logger.debug("Available problems * algorithms: %s", order)

    algorithms = parse_algorithms(args)
    problems = parse_problems(args)

    order = list(product(problems, algorithms))

    logger.info("Selected following tests:")
    for problem, algo in order:
        logger.info("  {problem:12} :: {algo:12}".format(problem=problem, algo=algo))

    logger.debug("Duplicating problems (-N flag)")
    return [
        SimulationCase(
            simulation_case[0],
            simulation_case[1],
            run_id,
            args["--renice"],
            resolve_results_dir(args),
            **params
        )
        for simulation_case in order
        for run_id in range(int(args["-N"]))
    ]


def parse_problems(args):
    problems = []
    if args["--problem"]:
        problems_filter = args["--problem"].lower().split(",")
        logger.debug("Selecting problems by name: %s", run_config.problems)
        problems = [
            problem
            for problem in run_config.problems
            if problem.lower() in problems_filter
        ]
        logger.debug("Selected: %s", problems)
    return problems


def parse_algorithms(args):
    algorithms = []
    if args["--algo"]:
        algorithms_filter = args["--algo"].lower().split(",")
        logger.debug("Selecting algorithms by name: %s", run_config.algorithms)
        algorithms = [
            algo for algo in run_config.algorithms if algo.lower() in algorithms_filter
        ]
        logger.debug("Selected: %s", algorithms)
    return algorithms


def parse_budgets(args):
    return sorted([int(budget) for budget in args["<budget>"].split(",")])


def prepare(algo: str, problem: str):
    drivers = algo.split("+")
    final_driver, problem_mod = None, None
    for driver_pos, driver in list(enumerate(drivers))[::-1]:
        final_driver, problem_mod = prepare_with_driver(
            driver, problem, final_driver, drivers, driver_pos
        )
    return final_driver, problem_mod


def prepare_with_driver(
    algo: str,
    problem: str,
    driver=None,
    all_drivers: List[str] = None,
    driver_pos: int = 0,
):
    logger.debug("Starting preparation")

    if not all_drivers:
        all_drivers = []

    try:
        logger.debug("Preparing %s for %s", algo, problem)
        logger.debug("driver class:%s", show_partial(driver))

        algo_class = prepare_algorithm_class(algo)

        problem_mod = prepare_problem_class(problem)

        config = {}

        load_obligatory_problem_parameters(config, problem_mod)

        if driver:
            update = {"driver": driver}
            config.update(update)
            logger.debug("Driver assignment: %s", driver)
            config.update(update)
            logger.debug("config: %s", show_conf(config))

            message_adapter_factory = prepare_message_adapter_class(
                algo, all_drivers, driver_pos
            )
            config.update({"driver_message_adapter_factory": message_adapter_factory})

        load_algorithm_config(algo, config)
        load_algorithm_with_subdrivers_config(algo, all_drivers, driver_pos, config)

        load_problem_config(algo, problem, config)
        load_problem_config(algo, problem, config, all_drivers, driver_pos)

        custom_init(algo, problem_mod, config)
        custom_init(algo, problem_mod, config, all_drivers, driver_pos)
        custom_init(algo, problem_mod, config, problem=problem)
        custom_init(algo, problem_mod, config, all_drivers, driver_pos, problem)

        load_init_population(problem_mod, config)

        try:
            algo_class(**config)
        except Exception as e:
            logger.exception("Class creation error.", exc_info=e)
            raise e
        else:
            logger.debug(
                "Preparing (algo=%s, problem=%s, driver=%s, all_drivers=%s, driver_pos=%d) done, class obj created",
                algo,
                problem,
                show_partial(driver),
                all_drivers,
                driver_pos,
            )

        instance = partial(algo_class, **config)
        logger.debug(
            "Dropping this dummy obj, returning partial instead: %s",
            show_partial(instance),
        )
        return instance, problem_mod

    except NotViableConfiguration as e:
        raise e

    except Exception as e:
        logger.exception(
            "Exception while preparing. "
            "algo={algo} "
            "problem={problem} "
            "driver={driver} "
            "all_drivers={all_drivers} "
            "driver_pos={driver_pos}".format(
                algo=algo,
                problem=problem,
                driver=show_partial(driver),
                all_drivers=all_drivers,
                driver_pos=driver_pos,
            ),
            exc_info=e,
        )
        raise e


def load_init_population(problem_mod, config: Dict[str, str]):
    if "population" not in config:
        config.update(
            {
                "population": gen_population(
                    run_config.DEFAULT_POPULATION_SIZE, problem_mod.dims
                )
            }
        )


def custom_init(
    algo: str,
    problem_mod: str,
    config: Dict[str, str],
    all_drivers: List[str] = None,
    driver_pos: int = None,
    problem: str = None,
):
    """
    Custom initialization functions for algorithm (and optional sub-drivers or problems)
        example fun: init_alg___SPEA2
        example fun: init_alg___HGS
        example fun: init_alg___IMGA

        example fun: init_alg___HGS__SPEA2
        example fun: init_alg___IMGA__HGS_SPEA2

        example fun: init_alg___SPEA2____ackley
        example fun: init_alg___HGS____zdt1

        example fun: init_alg___HGS__SPEA2____ackley
        example fun: init_alg___IMGA__HGS_SPEA2____zdt1
    """
    with suppress(AttributeError):
        key = "init_alg___" + algo
        if all_drivers:
            key += "__" + "_".join(all_drivers[driver_pos + 1 :])
        if problem:
            key += "____" + problem
        logger.debug("Try %s(…)", key)
        updater = getattr(run_config, key)
        logger.debug(
            "Custom initialization: %s: %s: %s", "| by algo fun:", key, updater
        )
        updater(config, problem_mod)
        logger.debug("config: %s", show_conf(config))


def load_problem_config(
    algo: str,
    problem: str,
    config: Dict[str, str],
    all_drivers: List[str] = None,
    driver_pos: int = 0,
):
    """
    Algorithm (with optional sub-drivers) + problem config
        example key: (SPEA2, ackley)
        example key: (SPEA2, zdt1)
        example key: (HGS, ackley)
        example key: (HGS, zdt1)
        example key: (IMGA, ackley)
        example key: (IMGA, zdt1)
        example key: (HGS, SPEA2,           ackley)

        example key: (IMGA, HGS, SPEA2,           ackley)
        example key: (IMGA, HGS, SPEA2,           zdt1)
    """
    all_drivers = [] if all_drivers is None else all_drivers
    with suppress(KeyError):
        key = (algo, *tuple(all_drivers[driver_pos + 1 :]), problem)
        logger.debug("Try cust_base[%s]", key)
        update = run_config.cust_base[key]
        logger.debug(
            "Dedicated problem config: %s %s %s: %s %s",
            "| by cust dict key:",
            key,
            "\n    <<",
            ", ".join(update),
            update,
        )
        config.update(update)
        logger.debug("config: %s", show_conf(config))


def load_algorithm_with_subdrivers_config(
    algo: str, all_drivers: List[str], driver_pos: int, config: Dict[str, str]
):
    """
    Algorithm + sub-drivers config
        example key: (SPEA2, ()          )
        example key: (HGS,   (SPEA2)     )
        example key: (IMGA,  (HGS, SPEA2))
    """
    with suppress(KeyError):
        key = (algo, tuple(all_drivers[driver_pos + 1 :]))
        logger.debug("Try algo_base[%s]", key)
        update = run_config.algo_base[key]
        logger.debug(
            "Algorithms with subdrivers config: %s %s %s: %s %s",
            "| by algo dict key:",
            key,
            "\n    <<",
            ", ".join(update),
            update,
        )
        config.update(update)
        logger.debug("config: %s", show_conf(config))


def load_algorithm_config(algo: str, config: Dict[str, str]):
    """
    Algorithm base config.
        example key: SPEA2
        example key: HGS
        example key: IMGA
    """
    with suppress(KeyError):
        key = algo
        logger.debug("Try algo_base[%s]", key)
        update = run_config.algo_base[key]
        logger.debug(
            "Algorithm config: %s: %s: %s",
            "| by algo dict key:",
            key,
            ", ".join(update),
        )
        config.update(update)
        logger.debug("config: %s", show_conf(config))


def load_obligatory_problem_parameters(config: Dict[str, str], problem_mod):
    update = {"dims": problem_mod.dims, "fitnesses": problem_mod.fitnesses}
    logger.debug("Per-problem config: %s", update)
    config.update(update)
    logger.debug("config: %s", show_conf(config))


def prepare_problem_class(problem: str):
    problem_mod = ".".join(["problems", problem, "problem"])
    problem_mod = import_module(problem_mod)
    return problem_mod


def prepare_algorithm_class(algo: str):
    algo_mod = ".".join(["algorithms", algo, algo])
    algo_mod = import_module(algo_mod)
    algo_class = getattr(algo_mod, algo)
    return algo_class


def prepare_message_adapter_class(algo: str, all_drivers: List[str], driver_pos: int):
    driver_algo = all_drivers[driver_pos + 1]
    try:
        message_mod_name = "algorithms.{}.message".format(driver_algo)
        adapter_class_name = "{}{}MessageAdapter".format(driver_algo, algo)

        logger.debug(
            "Searching for message adapter in... %s.%s",
            message_mod_name,
            adapter_class_name,
        )
        message_mod = import_module(message_mod_name)
        return getattr(message_mod, adapter_class_name)
    except:
        raise NotViableConfiguration()


def resolve_results_dir(args):
    return args["--dir"] or serialization.RESULTS_DIR
