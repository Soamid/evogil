import logging
import multiprocessing
import os
import random
import time
import collections
import operator

from importlib import import_module
from contextlib import suppress
from itertools import product, count
from algorithms.base.drivergen import DriverGen
from algorithms.base.driverlegacy import DriverLegacy

from evotools.ea_utils import gen_population
from evotools import run_config

from functools import partial
from evotools.log_helper import get_logger
from evotools.random_tools import show_partial
from evotools.serialization import RunResult
from evotools.timing import log_time, process_time
from evotools.timing import system_time

logger = get_logger(__name__)


def run_parallel(args):
    budgets = sorted([int(budget) for budget in args['<budget>'].split(',')])
    logger.debug("Budgets: %s", budgets)

    order = list(product(run_config.problems, run_config.algorithms))

    logger.debug("Problems * algorithms: %s",
                 order)

    algorithms = run_config.algorithms
    if args['--algo']:
        algorithms_filter = args['--algo'].lower().split(',')
        logger.debug("Selecting algorithms by name: %s",
                     algorithms)
        algorithms = [
            algo
            for algo in algorithms
            if algo.lower() in algorithms_filter
        ]
        logger.debug("Selected: %s",
                     algorithms)

    problems = run_config.problems
    if args['--problem']:
        problems_filter = args['--problem'].lower().split(',')
        logger.debug("Selecting problems by name: %s",
                     problems)
        problems = [
            problem
            for problem in problems
            if problem.lower() in problems_filter
        ]
        logger.debug("Selected: %s",
                     problems)

    order = list(product(problems, algorithms))

    logger.info("Selected following tests: \n%s",
                '\n,'.join("  {problem:12} :: {algo:12}".format(problem=problem, algo=algo)
                           for problem, algo
                           in order))

    logger.debug("Duplicating problems (-N flag)")
    order = [
        (test, budgets, runid, args["--renice"])
        for test in order
        for runid in range(int(args['-N']))
    ]

    logger.debug("Creating the pool")
    p = multiprocessing.Pool(int(args['-j']))

    wall_time = []
    with log_time(system_time, logger, "Pool evaluated in {time_res}s", out=wall_time):
        results = p.map(worker, order, chunksize=1)

    proc_times = sum(proc_time
                     for res, proc_time
                     in results
                     if res is not None)
    # errors = [proc_time
    #           for (res, proc_time), (test, budgets, runid)
    #           in zip(results, order)
    #           if res is None]
    errors = [str((test, budgets, runid))
              for comp_result, (test, budgets, runid, renice)
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
    for (bench, _, _), (res, proc_time) in zip(order, results):
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
    (problem, algo), budgets, runid, renice = args

    if renice:
        logger.debug("Renice the process PID:%d by %d", os.getpid(), int(args["--renice"]))
        os.nice(int(args["--renice"]))

    logger.debug("Getting random seed")
    # basically we duplicate the code of https://github.com/python/cpython/blob/master/Lib/random.py#L111 because
    # in case os.urandom is not available, random.seed defaults to epoch time. That would set the seed equal in each
    # process, which is not acceptable.
    try:
        random_seed = int.from_bytes(os.urandom(2500), 'big')
    except NotImplementedError:
        random_seed = int(time.time() * 256 + os.getpid())  # that's not enough for MT, but will have to do for now.
    random.seed(random_seed)

    drivers = algo.split('+')

    runres = RunResult(algo, problem, runid=runid)

    try:
        final_driver, problem_mod = None, None
        for driver_pos, driver in list(enumerate(drivers))[::-1]:
            final_driver, problem_mod = prepare(driver,
                                                problem,
                                                final_driver,
                                                drivers, driver_pos
            )

        logger.debug("Creating the driver used to perform computation")
        driver = final_driver()
        total_cost, result = 0, None

        proc_time = []
        results = []

        logger.info("Beginning processing of %s, args: %s", driver, args)
        with log_time(process_time, logger, "Processing done in {time_res}s CPU time", out=proc_time):
            if isinstance(driver, DriverGen):
                logger.debug("The driver %s is DriverGen-based", show_partial(driver))
                gen = driver.population_generator()
                proxy = None
                logger.debug("Starting processing")

                for budget in budgets:
                    logger.debug("Next budget step is %d", budget)
                    while True:  # loop until budget met or exceeded
                        logger.debug("Waiting for next proxy")
                        with log_time(process_time, logger, "Got proxy in {time_res}s CPU time"):
                            proxy = gen.send(proxy)
                        logger.debug("Proxy.cost: %d", proxy.cost)
                        total_cost += proxy.cost
                        logger.debug("total_cost: %d", total_cost)
                        if total_cost >= budget:
                            logger.debug("Cost %d equals/overpasses next budget step %d. Storing finalized population",
                                         total_cost,
                                         budgets[0])
                            finalpop = proxy.finalized_population()
                            finalpop_fit = [[fit(x) for fit in problem_mod.fitnesses] for x in finalpop]
                            runres.store(budget, total_cost, finalpop, finalpop_fit)
                            results.append((total_cost, finalpop))
                            break
                logger.debug("End loop, total_cost:%d", total_cost)
                logger.debug("Final population: %s", proxy.finalized_population())

            elif isinstance(driver, DriverLegacy):
                logger.debug("The driver %s is DriverLegacy-based", show_partial(driver))
                with log_time(process_time, logger, "All iterations in {time_res}s CPU time"):
                    for budget in budgets:
                        logger.debug("Re-creating the driver used to perform computation")
                        driver = final_driver()
                        driver.budget = budget
                        with log_time(process_time, logger,
                                      "Iteration with budget {0} in {{time_res}}s CPU time".format(budget)):
                            logger.debug("Running with budget=%d", budget)
                            total_cost = driver.steps(count(), budget)
                        finalpop = driver.finish()
                        finalpop_fit = [[fit(x) for fit in problem_mod.fitnesses] for x in finalpop]
                        runres.store(budget, total_cost, finalpop, finalpop_fit)
                        results.append((budget, finalpop))
            else:
                e = NotImplementedError()
                logger.exception("Oops. The driver type is not recognized, got %s", show_partial(driver), exc_info=e)
                raise e

        return results, proc_time[-1]

    except Exception as e:
        logger.exception("Some error", exc_info=e)

    finally:
        logger.info("Finished processing. args:%s", args)


def prepare(algo, problem, driver=None, all_drivers=None, driver_pos=0):
    logger.debug("Starting preparation")

    if not all_drivers:
        all_drivers = []

    try:

        logger.debug("Preparing %s for %s", algo, problem)
        logger.debug("driver class:%s", show_partial(driver))

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
            logger.debug("%s %s: %s: %s",
                         descr,
                         "| by algo dict key:", key, ', '.join(update))
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
            logger.debug("%s %s %s %s: %s %s",
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
            logger.debug("%s %s %s %s: %s %s",
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
            logger.debug("%s %s %s %s: %s %s",
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
            logger.debug("%s %s %s %s: %s %s",
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
            logger.debug("%s %s %s %s: %s %s",
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
            logger.info(
                "Preparing (algo=%s, problem=%s, driver=%s, all_drivers=%s, driver_pos=%d) done, class obj created",
                algo,
                problem,
                show_partial(driver),
                all_drivers,
                driver_pos)

        instance = partial(algo_class, **config)
        logger.debug("Dropping this dummy obj, returning partial instead: %s",
                     instance)
        return instance, problem_mod

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
