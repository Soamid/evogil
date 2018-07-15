from contextlib import suppress
from functools import partial
from importlib import import_module
from itertools import product
from typing import List, Dict

from pip._internal.utils import logging

from evotools.random_tools import show_partial, show_conf
from simulation import run_config
from simulation.run_config import NotViableConfiguration

logger = logging.getLogger(__name__)


class SimulationCase:
    def __init__(self, problem_name: str, algorithm_name: str, budgets: List[int], run_id: int, renice: str):
        self.problem_name = problem_name
        self.algorithm_name = algorithm_name
        self.budgets = budgets
        self.run_id = run_id
        self.renice = renice


def create_simulation(args):
    budgets = parse_budgets(args)
    logger.debug("Budgets: %s", budgets)

    order = list(product(run_config.problems, run_config.algorithms))

    logger.debug("Available problems * algorithms: %s",
                 order)

    algorithms = parse_algorithms(args)
    problems = parse_problems(args)

    order = list(product(problems, algorithms))

    logger.info("Selected following tests:")
    for problem, algo in order:
        logger.info("  {problem:12} :: {algo:12}".format(problem=problem, algo=algo))

    logger.debug("Duplicating problems (-N flag)")
    return [
        SimulationCase(simulation_case[0], simulation_case[1], budgets, run_id, args["--renice"])
        for simulation_case in order
        for run_id in range(int(args['-N']))
    ]


def parse_problems(args):
    problems = []
    if args['--problem']:
        problems_filter = args['--problem'].lower().split(',')
        logger.debug("Selecting problems by name: %s", run_config.problems)
        problems = [
            problem
            for problem in run_config.problems
            if problem.lower() in problems_filter
        ]
        logger.debug("Selected: %s",
                     problems)
    return problems


def parse_algorithms(args):
    algorithms = []
    if args['--algo']:
        algorithms_filter = args['--algo'].lower().split(',')
        logger.debug("Selecting algorithms by name: %s", run_config.algorithms)
        algorithms = [
            algo
            for algo in run_config.algorithms
            if algo.lower() in algorithms_filter
        ]
        logger.debug("Selected: %s",
                     algorithms)
    return algorithms


def parse_budgets(args):
    return sorted([int(budget) for budget in args['<budget>'].split(',')])


def prepare(algo, problem, driver=None, all_drivers=None, driver_pos=0):
    logger.debug("Starting preparation")

    if not all_drivers:
        all_drivers = []

    try:
        logger.debug("Preparing %s for %s", algo, problem)
        logger.debug("driver class:%s", show_partial(driver))

        algo_class = prepare_algorithm_class(algo)

        problem_mod = prepare_problem_class(problem)

        config = {}

        load_meta_config(config)
        load_obligatory_problem_parameters(config, problem_mod)

        if driver:
            update = {"driver": driver}
            config.update(update)
            logger.debug("Driver assignment: %s", driver)
            config.update(update)
            logger.debug("config: %s", show_conf(config))

            message_adapter_factory = prepare_message_adapter_class(algo, all_drivers, driver_pos)
            config.update({"message_adapter_factory": message_adapter_factory})

        load_algorithm_config(algo, config)

        ################################################################################
        # ALGORITHM + SUBDRIVERS CONFIG
        #
        # example key: (SPEA2, ()          )
        # example key: (HGS,   (SPEA2)     )
        # example key: (IMGA,  (HGS, SPEA2))
        load_algorithm_with_subdrivers_config(algo, all_drivers, driver_pos, config)

        ################################################################################
        # ALGORITHM + PROBLEM CONFIG
        #
        # example key: (SPEA2, ackley)
        # example key: (SPEA2, zdt1)
        # example key: (HGS, ackley)
        # example key: (HGS, zdt1)
        # example key: (IMGA, ackley)
        # example key: (IMGA, zdt1)
        load_problem_config(algo, problem, config)

        ################################################################################
        # ALGORITHM WITH SUBDRIVERS + PROBLEM CONFIG
        #
        # example key: (HGS, SPEA2,           ackley)
        # example key: (IMGA, HGS, SPEA2,           ackley)
        # example key: (IMGA, HGS, SPEA2,           zdt1)
        load_problem_config(algo, problem, config, all_drivers, driver_pos)

        ################################################################################
        # CUSTOM INITIALIZATION FOR ALGORITHM
        #
        # example fun: init_alg___SPEA2
        # example fun: init_alg___HGS
        # example fun: init_alg___IMGA
        custom_init(algo, problem_mod, config)

        ################################################################################
        # CUSTOM INITIALIZATION FOR ALGORITHM WITH SUBDRIVERS
        #
        # example fun: init_alg___HGS__SPEA2
        # example fun: init_alg___IMGA__HGS_SPEA2
        custom_init(algo, problem_mod, config, all_drivers, driver_pos)

        ################################################################################
        # CUSTOM INITIALIZATION FOR ALGORITHM AND PROBLEM
        #
        # example fun: init_alg___SPEA2____ackley
        # example fun: init_alg___HGS____zdt1
        custom_init(algo, problem_mod, config, problem=problem)

        ################################################################################
        # CUSTOM INITIALIZATION FOR ALGORITHM WITH SUBDRIVERS AND PROBLEM
        #
        # example fun: init_cust___SPEA2____ackley  # configure SPEA2 for ackley
        # example fun: init_cust___SPEA2____zdt1
        # example fun: init_cust_IMGA_HGS___SPEA2____ackley  # configure SPEA2 for ackley when under IMGA+HGS
        # example fun: init_cust_IMGA_HGS___SPEA2____zdt1
        # example fun: init_cust_IMGA___HGS__SPEA2____ackley  # configure HGS for ackley when under IMGA w/ SPEA2 driver
        # example fun: init_cust_IMGA___HGS__SPEA2____zdt1
        # example fun: init_cust___IMGA__HGS_SPEA2____ackley  # configure IMGA for ackley w/ HGS+SPEA2 driver
        # example fun: init_cust___IMGA__HGS_SPEA2____zdt1
        custom_init(algo, problem_mod, config, all_drivers, driver_pos, problem)

        ################################################################################
        # DROPPING TRASH
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("dropping trash from config: %s",
                         {k: v
                          for k, v
                          in config.items()
                          if k.startswith('__metaconfig__')
                          })
        config = {k: v
                  for k, v
                  in config.items()
                  if not k.startswith('__metaconfig__')
                  }

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
                driver_pos)

        instance = partial(algo_class, **config)
        logger.debug("Dropping this dummy obj, returning partial instead: %s", show_partial(instance))
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
            "driver_pos={driver_pos}".format(algo=algo,
                                             problem=problem,
                                             driver=show_partial(driver),
                                             all_drivers=all_drivers,
                                             driver_pos=driver_pos),
            exc_info=e)
        raise e


def custom_init(algo, problem_mod, config, all_drivers=None, driver_pos=None, problem=None):
    with suppress(AttributeError):
        key = "init_alg___" + algo
        if all_drivers:
            key += '__' + '_'.join(all_drivers[driver_pos + 1:])
        if problem:
            key += "____" + problem
        logger.debug("Try %s(…)", key)
        updater = getattr(run_config, key)
        logger.debug("Custom initialization: %s: %s: %s",
                     "| by algo fun:",
                     key,
                     updater
                     )
        updater(config, problem_mod)
        logger.debug("config: %s", show_conf(config))


def load_problem_config(algo, problem, config, all_drivers=None, driver_pos=0):
    all_drivers = [] if all_drivers is None else all_drivers
    with suppress(KeyError):
        key = (algo,
               *tuple(all_drivers[driver_pos + 1:]),
               problem
               )
        logger.debug("Try cust_base[%s]", key)
        update = run_config.cust_base[key]
        logger.debug("Dedicated problem config: %s %s %s: %s %s",
                     "| by cust dict key:", key, "\n    <<", ', '.join(update),
                     update)
        config.update(update)
        logger.debug("config: %s", show_conf(config))


def load_algorithm_with_subdrivers_config(algo, all_drivers, driver_pos, config):
    with suppress(KeyError):
        key = (algo,
               tuple(all_drivers[driver_pos + 1:])
               )
        logger.debug("Try algo_base[%s]", key)
        update = run_config.algo_base[key]
        logger.debug("Algorithms with subdrivers config: %s %s %s: %s %s",
                     "| by algo dict key:", key, "\n    <<", ', '.join(update),
                     update)
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
        logger.debug("Algorithm config: %s: %s: %s",
                     "| by algo dict key:", key, ', '.join(update))
        config.update(update)
        logger.debug("config: %s", show_conf(config))


def load_obligatory_problem_parameters(config, problem_mod):
    update = {"dims": problem_mod.dims, "fitnesses": problem_mod.fitnesses}
    logger.debug("Per-problem config: %s", update)
    config.update(update)
    logger.debug("config: %s", show_conf(config))


def load_meta_config(config):
    logger.debug("Starting with config containing meta-parameters")
    config.update({"__metaconfig__populationsize": run_config.metaconfig_populationsize})
    logger.debug("config: %s", show_conf(config))


def prepare_problem_class(problem):
    problem_mod = '.'.join(['problems', problem, 'problem'])
    problem_mod = import_module(problem_mod)
    return problem_mod


def prepare_algorithm_class(algo):
    algo_mod = '.'.join(['algorithms', algo, algo])
    algo_mod = import_module(algo_mod)
    algo_class = getattr(algo_mod, algo)
    return algo_class


def prepare_message_adapter_class(algo: str, all_drivers: List[str], driver_pos: int):
    driver_algo = all_drivers[driver_pos + 1]
    try:
        message_mod = import_module("algorithms.{}.message".format(driver_algo))
        return getattr(message_mod, "{}{}MessageAdapter".format(algo, driver_algo))
    except:
        raise NotViableConfiguration()
