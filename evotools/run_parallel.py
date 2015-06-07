# base
import copy
import logging
import multiprocessing
import time
import collections
import operator

from importlib import import_module
from contextlib import suppress
from algorithms.base.drivergen import DriverGen

from evotools.ea_utils import gen_population
from evotools import run_config

from functools import partial
import traceback
from evotools.log_helper import get_logger
from evotools.timing import log_time, process_time
from evotools.timing import system_time

logger = get_logger(__name__)


def run_parallel(args):
    budgets = sorted([int(budget) for budget in args['<budget>'].split(',')])
    logger.debug("Budgets: %s", budgets)

    order = [
        ('ZDT6', 'HGS+NSGAII'),
        ('ZDT4', 'HGS+NSGAII'),
        ('ZDT4', 'IMGA+NSGAII'),
        ('ZDT3', 'HGS+NSGAII'),
        ('ZDT1', 'HGS+NSGAII'),
        ('ZDT2', 'HGS+NSGAII'),
        ('ZDT4', 'NSGAII'),
        ('ZDT6', 'NSGAII'),
        ('kursawe', 'HGS+NSGAII'),
        ('ZDT3', 'NSGAII'),
        ('ZDT1', 'NSGAII'),
        ('ZDT2', 'NSGAII'),
        ('ZDT6', 'IMGA+NSGAII'),
        ('ZDT3', 'IMGA+NSGAII'),
        ('ZDT2', 'IMGA+NSGAII'),
        ('ZDT1', 'IMGA+NSGAII'),
        ('ZDT2', 'HGS+SPEA2'),
        ('ZDT1', 'HGS+SPEA2'),
        ('kursawe', 'IMGA+NSGAII'),
        ('kursawe', 'NSGAII'),
        ('ZDT4', 'HGS+SPEA2'),
        ('ZDT4', 'IBEA'),
        ('ZDT4', 'IMGA+IBEA'),
        ('kursawe', 'IBEA'),
        ('kursawe', 'IMGA+IBEA'),
        ('kursawe', 'SPEA2'),
        ('kursawe', 'IMGA+SPEA2'),
        ('ZDT6', 'IBEA'),
        ('ZDT6', 'IMGA+IBEA'),
        ('kursawe', 'HGS+SPEA2'),
        ('ZDT3', 'HGS+SPEA2'),
        ('ZDT3', 'IBEA'),
        ('ZDT3', 'IMGA+IBEA'),
        ('ZDT4', 'IMGA+SPEA2'),
        ('ZDT2', 'IMGA+IBEA'),
        ('ZDT2', 'IBEA'),
        ('ZDT1', 'IBEA'),
        ('kursawe', 'HGS+IBEA'),
        ('ZDT1', 'IMGA+IBEA'),
        ('ZDT4', 'HGS+IBEA'),
        ('ZDT6', 'HGS+SPEA2'),
        ('ZDT3', 'HGS+IBEA'),
        ('ZDT1', 'HGS+IBEA'),
        ('ZDT2', 'HGS+IBEA'),
        ('ZDT1', 'IMGA+SPEA2'),
        ('ZDT2', 'IMGA+SPEA2'),
        ('ZDT3', 'IMGA+SPEA2'),
        ('ZDT6', 'IMGA+SPEA2'),
        ('ackley', 'IMGA+NSGAII'),
        ('ackley', 'HGS+NSGAII'),
        ('ZDT4', 'SPEA2'),
        ('ZDT1', 'SPEA2'),
        ('ZDT6', 'SPEA2'),
        ('ZDT2', 'SPEA2'),
        ('ZDT3', 'SPEA2'),
        ('ackley', 'NSGAII'),
        ('ZDT6', 'HGS+IBEA'),
        ('ackley', 'IMGA+SPEA2'),
        ('ackley', 'HGS+SPEA2'),
        ('ackley', 'SPEA2'),
        ('ackley', 'IMGA+IBEA'),
        ('ackley', 'IBEA'),
        ('ackley', 'HGS+IBEA'),
        ('parabol', 'HGS+SPEA2'),
        ('parabol', 'HGS+IBEA'),
        ('parabol', 'HGS+NSGAII')
    ]
    logger.debug("Problems * algorithms: %s",
                 order)

    if args['--algo']:
        algos = args['--algo'].lower().split(',')
        logger.debug("Selecting algorithms by name: %s",
                     algos)
        order = [(problem, algo)
                 for problem, algo
                 in order
                 if algo.lower() in algos
        ]
        logger.debug("Selected: %s",
                     order)

    if args['--problem']:
        problems = args['--problem'].lower().split(',')
        logger.debug("Selecting problems by name: %s",
                     problems)
        order = [(problem, algo)
                 for problem, algo
                 in order
                 if problem.lower() in problems
        ]
        logger.debug("Selected: %s",
                     order)

    logger.info("Selected following tests: %s",
                ', '.join("  {problem:12} :: {algo:12}".format(problem=problem, algo=algo)
                          for problem, algo in order))

    logger.debug("Duplicating problems (-N flag)")
    order = [(test, budgets)
             for test in order
             for i in range(int(args['-N']))
    ]

    logger.debug("Creating the pool")
    p = multiprocessing.Pool(int(args['-j']))

    wall_time = []
    with log_time(system_time, logger, "Pool evaluated in {time_res}s", out=wall_time):
        results = p.map(worker, order, chunksize=1)

    proc_times = sum(proc_time
                     for res, proc_time
                     in results
                     if res is not None
    )
    errors = [str((alg, prob))
              for comp_result, (prob, alg)
              in zip(results, order)
              if comp_result is None
    ]

    speedup = proc_times / wall_time[0]

    logger.info("""########################################
SUMMARY:
  wall time:     %7.3f
  CPU+user time: %7.3f
  est. speedup:  %7.3f""", wall_time[0], proc_times, speedup)

    if logger.isEnabledFor(logging.DEBUG) and errors:
        errors = '\n                 '.join(errors)
        logger.error("Errors encountered: {errors:>3}".format(**locals()))

    summary = collections.defaultdict(float)
    for (bench, _), (res, proc_time) in zip(order, results):
        summary[bench] += proc_time or 0.0

    if logger.isEnabledFor(logging.INFO):
        logger.info("Running time:")
        res = []
        for (prob, alg), timesum in sorted(summary.items(),
                                           key=operator.itemgetter(1),
                                           reverse=True
        ):
            prob_show = "'" + prob + "'"
            alg_show = "'" + alg + "'"
            avg_time = timesum / float(args['-N'])
            res.append("  ({prob_show:16}, {alg_show:16}),  # {avg_time:7.3f}s".format(**locals()))
        logger.info('\n'.join(res))


def worker(args):
    logger.debug("Starting the worker. args:%s", args)
    (problem, algo), budgets = args

    drivers = algo.split('+')

    try:
        final_driver = None
        for driver_pos, driver in list(enumerate(drivers))[::-1]:
            final_driver = prepare(driver,
                                   problem,
                                   final_driver,
                                   drivers, driver_pos
            )

        logger.debug("Creating the driver used to perform computation")
        driver = final_driver()
        total_cost, result = 0, None

        proc_time = []
        results = []
        with log_time(system_time, logger, "Processing done in {time_res}s", out=proc_time):
            if isinstance(driver, DriverGen):
                max_budget = max(budgets)
                gen = driver.population_generator()
                proxy = None
                logger.debug("Starting processing")

                while total_cost <= max_budget:
                    logger.debug("Waiting for next proxy")
                    with log_time(system_time, logger, "Got proxy in {time_res}s"):
                        proxy = gen.send(proxy)
                    logger.debug("Proxy.cost: %d", proxy.cost)
                    total_cost += proxy.cost
                    logger.debug("total_cost: %d", total_cost)
                    if total_cost >= budgets[0]:
                        logger.debug("Cost %d equals/overpasses next budget step %d. Storing finalized population",
                                     total_cost,
                                     budgets[0])
                        results.append(proxy.finalized_population())
                logger.debug("End loop, total_cost:%d", total_cost)
                logger.debug("Final population: %s", proxy.finalized_population())
            else:
                e = NotImplementedError()
                logger.exception("Oops. The driver type is not recognized", exc_info=e)
                raise e

        return results, proc_time[-1]

    except Exception as e:
        logger.exception("Some error", exc_info=e)


def prepare(algo, problem, driver=None, all_drivers=None, driver_pos=0):
    logger.debug("Starting preparation")

    if not all_drivers:
        all_drivers = []

    logger.debug("Preparing %s for %s", algo, problem)
    logger.debug("driver:%s", driver)

    algo_mod = '.'.join(['algorithms', algo, algo])
    algo_mod = import_module(algo_mod)
    algo_class = getattr(algo_mod, algo)

    problem_mod = '.'.join(['problems', problem, 'problem'])
    problem_mod = import_module(problem_mod)

    # START WITH META-CONFIG
    logger.debug("Starting with config containing meta-parameters")
    config = {
        "__metaconfig__populationsize": run_config.metaconfig_populationsize
    }
    logger.debug("config: %s", config)

    ################################################################################
    # CUSTOMS FOR PROBLEM
    update = {"dims": problem_mod.dims, "fitnesses": problem_mod.fitnesses}
    logger.debug("Per-problem config: %s", update)
    config.update(update)
    logger.debug("config: %s", config)

    ################################################################################
    descr = "DRIVER ASSIGNMENT"
    if driver:
        update = {"driver": driver}
        config.update(update)
        logger.debug("Assigning driver: %s", update)
        config.update(update)
        logger.debug("config: %s", config)

    ################################################################################
    descr = "CUSTOMS FOR ALGORITHM"
    # example key: SPEA2
    # example key: HGS
    # example key: IMGA
    with suppress(KeyError):
        key = algo
        update = run_config.algo_base[key]
        logger.debug("%s %s: %s",
                     descr,
                     "| by algo dict key:", key, "\n    <<", ', '.join(update),
                     update)
        config.update(update)
        logger.debug("config: %s", config)

    ################################################################################
    descr = "CUSTOMS FOR ALGORITHM + SUBDRIVERS"
    # example key: (SPEA2, ()          )
    # example key: (HGS,   (SPEA2)     )
    # example key: (IMGA,  (HGS, SPEA2))
    with suppress(KeyError):
        key = (algo,
               tuple(all_drivers[driver_pos + 1:])
        )
        update = run_config.algo_base[key]
        logger.debug("%s %s: %s",
                     descr,
                     "| by algo dict key:", key, "\n    <<", ', '.join(update),
                     update)
        config.update(update)
        logger.debug("config: %s", config)

    ################################################################################
    descr = "CUSTOMS FOR PARENTS + ALGORITHM"
    # example key: ((IMGA, HGS), SPEA2)
    # example key: ((IMGA,),     HGS  )
    # example key: ((),          IMGA )
    with suppress(KeyError):
        key = (tuple(all_drivers[:driver_pos]),
               algo
        )
        update = run_config.algo_base[key]
        logger.debug("%s %s: %s",
                     descr,
                     "| by algo dict key:", key, "\n    <<", ', '.join(update),
                     update)
        config.update(update)
        logger.debug("config: %s", config)

    ################################################################################
    descr = "CUSTOMS FOR PARENTS + ALGORITHM + SUBDRIVERS"
    # example key: ((IMGA, HGS), SPEA2, ()          )
    # example key: ((IMGA,),     HGS,   (SPEA2)     )
    # example key: ((),          IMGA,  (HGS, SPEA2))
    with suppress(KeyError):
        key = (tuple(all_drivers[:driver_pos]),
               algo,
               tuple(all_drivers[driver_pos + 1:])
        )
        update = run_config.algo_base[key]
        logger.debug("%s %s: %s",
                     descr,
                     "| by algo dict key:", key, "\n    <<", ', '.join(update),
                     update)
        config.update(update)
        logger.debug("config: %s", config)

    ################################################################################
    descr = "CUSTOMS (simpl)"
    # example key: (SPEA2, ackley)
    # example key: (SPEA2, zdt1)
    # example key: (HGS, ackley)
    # example key: (HGS, zdt1)
    # example key: (IMGA, ackley)
    # example key: (IMGA, zdt1)
    with suppress(KeyError):
        key = ( algo,
                problem
        )
        update = run_config.cust_base[key]
        logger.debug("%s %s: %s",
                     descr,
                     "| by cust dict key:", key, "\n    <<", ', '.join(update),
                     update)
        config.update(update)
        logger.debug("config: %s", config)

    ################################################################################
    descr = "CUSTOMS"
    # example key: ((IMGA, HGS), SPEA2, (),           ackley)
    # example key: ((IMGA, HGS), SPEA2, (),           zdt1)
    # example key: ((IMGA),      HGS,   (SPEA2),      ackley)
    # example key: ((IMGA),      HGS,   (SPEA2),      zdt1)
    # example key: ((),          IMGA,  (HGS, SPEA2), ackley)
    # example key: ((),          IMGA,  (HGS, SPEA2), zdt1)
    with suppress(KeyError):
        key = (tuple(all_drivers[:driver_pos]),
               algo,
               tuple(all_drivers[driver_pos + 1:]),
               problem
        )
        update = run_config.cust_base[key]
        logger.debug("%s %s: %s",
                     descr,
                     "| by cust dict key:", key, "\n    <<", ', '.join(update),
                     update)
        config.update(update)
        logger.debug("config: %s", config)

    ################################################################################
    descr = "CUSTOMS FOR ALGORITHM"
    # example fun: init_alg_SPEA2
    # example fun: init_alg_HGS
    # example fun: init_alg_IMGA
    with suppress(AttributeError):
        key = "init_alg_" + algo
        updater = getattr(run_config, key)
        logger.debug("%s %s: %s: %s",
                     descr,
                     "| by algo fun:",
                     key,
                     updater
        )
        updater(config, problem_mod)
        logger.debug("config: %s", config)

    ################################################################################
    descr = "CUSTOMS FOR ALGORITHM + SUBDRIVERS"
    # example fun: init_alg_HGS__SPEA2
    # example fun: init_alg_IMGA__HGS_SPEA2
    with suppress(AttributeError):
        key = "init_alg_" + algo + '__' + '_'.join(all_drivers[driver_pos + 1:])
        updater = getattr(run_config, key)
        logger.debug("%s %s: %s: %s",
                     descr,
                     "| by algo fun:",
                     key,
                     updater
        )
        updater(config, problem_mod)
        logger.debug("config: %s", config)

    ################################################################################
    descr = "CUSTOMS FOR PARENTS + ALGORITHM"
    # example fun: init_alg_IMGA_HGS__SPEA2
    # example fun: init_alg_IMGA__HGS
    with suppress(AttributeError):
        key = "init_alg_" + '_'.join(all_drivers[:driver_pos]) + '__' + algo
        updater = getattr(run_config, key)
        logger.debug("%s %s: %s: %s",
                     descr,
                     "| by algo fun:",
                     key,
                     updater
        )
        updater(config, problem_mod)
        logger.debug("config: %s", config)

    ################################################################################
    descr = "CUSTOMS FOR PARENTS + ALGORITHM + SUBDRIVERS"
    # example fun: init_alg_IMGA__HGS__SPEA2
    with suppress(AttributeError):
        key = "init_alg_" + '_'.join(all_drivers[:driver_pos]) + '__' + algo + '__' + '_'.join(
            all_drivers[driver_pos + 1:])
        updater = getattr(run_config, key)
        logger.debug("%s %s: %s: %s",
                     descr,
                     "| by algo fun:",
                     key,
                     updater
        )
        updater(config, problem_mod)
        logger.debug("config: %s", config)

    ################################################################################
    descr = "CUSTOMS FOR PROBLEM"
    # example key: ackley
    # example key: zdt1
    with suppress(KeyError):
        key = problem
        update = run_config.prob_base[key]
        logger.debug("%s %s: %s",
                     descr,
                     "| by prob dict key:", key, "\n    <<", ', '.join(run_config.prob_base[key]),
                     update)
        config.update(update)
        logger.debug("config: %s", config)

    ################################################################################
    descr = "CUSTOMS FOR PROBLEM"
    # example fun: init_prob_ackley
    with suppress(AttributeError):
        key = "init_prob_" + '_'.join(all_drivers[:driver_pos]) + '__' + algo + '__' + '_'.join(
            all_drivers[driver_pos + 1:])
        updater = getattr(run_config, key)
        logger.debug("%s %s: %s: %s",
                     descr,
                     "| by prob fun:",
                     key,
                     updater
        )
        updater(config, problem_mod)
        logger.debug("config: %s", config)

    ################################################################################
    descr = "CUSTOMS"
    # example fun: init_cust_SPEA2___ackley
    # example fun: init_cust_SPEA2___zdt1
    # example fun: init_cust_IMGA_HGS__SPEA2___ackley
    # example fun: init_cust_IMGA_HGS__SPEA2___zdt1
    # example fun: init_cust_IMGA__HGS__SPEA2___ackley
    # example fun: init_cust_IMGA__HGS__SPEA2___zdt1
    # example fun: init_cust__IMGA__HGS_SPEA2___ackley
    # example fun: init_cust__IMGA__HGS_SPEA2___zdt1
    with suppress(AttributeError):
        key = "init_cust_" + '_'.join(all_drivers[:driver_pos]) + '__' + algo + '__' + '_'.join(
            all_drivers[driver_pos + 1:])
        updater = getattr(run_config, key)
        logger.debug("%s %s: %s: %s",
                     descr,
                     "| by cust fun:",
                     key,
                     updater
        )
        updater(config, problem_mod)
        logger.debug("config: %s", config)

    ################################################################################
    descr = "GENERATING POPULATION"
    if "population" not in config:
        initial_population = gen_population(config["__metaconfig__populationsize"], problem_mod.dims)
        update = {"population": initial_population}
        logger.debug("%s (size: %s, dims: %s): %s",
                     descr,
                     config["__metaconfig__populationsize"],
                     problem_mod.dims,
                     initial_population)
        config.update(update)

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
        logger.info("Preparing (algo=%s, problem=%s, driver=%s, all_drivers=%s, driver_pos=%d) done, class obj created",
                    algo,
                    problem,
                    driver,
                    all_drivers,
                    driver_pos)

    instance = partial(algo_class, **config)
    logger.info("Dropping this dummy obj, returning partial instead: %s",
                instance)
    return instance

