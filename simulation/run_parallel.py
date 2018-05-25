import collections
import inspect
import logging
import multiprocessing
import operator
import os
import random
import time
from contextlib import suppress
from datetime import datetime
from functools import partial
from importlib import import_module
from itertools import product

from algorithms.base.drivergen import DriverGen, DriverProxy, Driver, DriverRxWrapper, BudgetRun, \
    DriverRx
from evotools.ea_utils import gen_population
from evotools.random_tools import show_partial, show_conf, close_and_join
from simulation import run_config
from simulation.run_config import NotViableConfiguration
from simulation.serialization import RunResult, RESULTS_DIR
from simulation.timing import log_time, process_time
from simulation.timing import system_time


def run_parallel(args, queue):
    logger = logging.getLogger(__name__)

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

    logger.info("Selected following tests:")
    for problem, algo in order:
        logger.info("  {problem:12} :: {algo:12}".format(problem=problem, algo=algo))

    logger.debug("Duplicating problems (-N flag)")
    order = [
        (test, budgets, runid, args["--renice"])
        for test in order
        for runid in range(int(args['-N']))
    ]

    logger.debug("Shuffling the job queue")
    random.shuffle(order)

    logger.debug("Creating the pool")

    with close_and_join(multiprocessing.Pool(int(args['-j']))) as p:

        wall_time = []
        start_time = datetime.now()
        results = []
        with log_time(system_time, logger, "Pool evaluated in {time_res}s", out=wall_time):
            worker(order[0])
            for i, subres in enumerate(p.imap(worker, order, chunksize=1)):
                results.append(subres)

                current_time = datetime.now()
                diff_time = current_time - start_time
                ratio = i * 1. / len(order)
                try:
                    est_delivery_time = start_time + diff_time / ratio
                    time_to_delivery = est_delivery_time - current_time
                    logging.info("Job queue progress: %.3f%%. Est. finish in %02d:%02d:%02d (at %s)",
                                 ratio * 100,
                                 time_to_delivery.days * 24 + time_to_delivery.seconds // 3600,
                                 time_to_delivery.seconds // 60,
                                 time_to_delivery.seconds % 60,
                                 est_delivery_time.strftime("%Y-%m-%d %H:%M:%S.%f")
                                 )
                except ZeroDivisionError:
                    logging.info("Job queue progress: %.3f%%. Est. finish: unknown yet", ratio)

    proc_times = sum(subres[1]
                     for subres
                     in results
                     if subres is not None)
    errors = [(test, budgets, runid)
              for comp_result, (test, budgets, runid, renice)
              in zip(results, order)
              if comp_result is None
              ]

    speedup = proc_times / wall_time[0]

    logger.info("SUMMARY:")
    logger.info("  wall time:     %7.3f", wall_time[0])
    logger.info("  CPU+user time: %7.3f", proc_times)
    logger.info("  est. speedup:  %7.3f", speedup)

    if errors:
        logger.error("Errors encountered:")
        for (probl, algo), budgets, runid in errors:
            logger.error("  %9s :: %14s :: runID=%d :: budgets=%s", probl, algo, runid,
                         ','.join(str(x) for x in budgets))

    summary = collections.defaultdict(float)
    for (bench, _, _, _), subres in zip(order, results):
        if subres:
            summary[bench] += subres[1]

    if logger.isEnabledFor(logging.INFO):
        logger.info("Running time:")
        res = []
        for (prob, alg), timesum in sorted(summary.items(),
                                           key=operator.itemgetter(1),
                                           reverse=True):
            prob_show = "'" + prob + "'"
            alg_show = "'" + alg + "'"
            avg_time = timesum / float(args['-N'])
            logger.info("  prob:{prob_show:16} algo:{alg_show:16}) time:{avg_time:>8.3f}s".format(**locals()))


def worker(args):
    logger = logging.getLogger(__name__)

    logger.debug("Starting the worker. args:%s", args)
    (problem, algo), budgets, runid, renice = args

    if renice:
        logger.debug("Renice the process PID:%s by %s", os.getpid(), renice)
        os.nice(int(renice))

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

    runres = RunResult(algo, problem, runid=runid, results_path=RESULTS_DIR)

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

        logger.debug("Beginning processing of %s, args: %s", driver, args)
        with log_time(process_time, logger, "Processing done in {time_res}s CPU time", out=proc_time):
            if isinstance(driver, DriverGen):
                logger.debug("The driver %s is DriverGen-based", show_partial(driver))
                driver.max_budget = budgets[-1]
                gen = driver.population_generator()
                proxy = None
                logger.debug("Starting processing")

                for budget in budgets:
                    logger.debug("Curr budget step is %d", budget)
                    while total_cost < budget:
                        logger.debug("Waiting for next proxy")
                        proxy = gen.send(proxy)
                        logger.debug("Proxy.cost: %d", proxy.cost)
                        total_cost += proxy.cost
                        logger.debug("total_cost: %d", total_cost)

                    logger.debug("Cost %d equals/overpasses next budget step %d. Storing finalized population",
                                 total_cost,
                                 budget)
                    finalpop = proxy.finalized_population()
                    finalpop_fit = [[fit(x) for fit in problem_mod.fitnesses] for x in finalpop]
                    runres.store(budget, total_cost, finalpop, finalpop_fit)
                    results.append((total_cost, finalpop))

                logger.debug("End loop, total_cost:%d", total_cost)
                logger.debug("Final population: %s", proxy.finalized_population())
            elif isinstance(driver, Driver):

                class BudgetIterator:
                    i = 0

                    def current(self):
                        return budgets[self.i]

                    def next(self):
                        self.i += 1

                    def has_next(self):
                        return self.i + 1 < len(budgets)

                budget_it = BudgetIterator()

                def get_budget_stage(proxy):
                    if proxy.cost >= budget_it.current() and budget_it.has_next():
                        budget_it.next()
                    return budget_it.current(), proxy

                def process_proxy(budget: int, proxy: DriverProxy):
                    finalpop = proxy.finalized_population()
                    finalpop_fit = [[fit(x) for fit in problem_mod.fitnesses] for x in finalpop]
                    runres.store(budget, proxy.cost, finalpop, finalpop_fit)
                    results.append((proxy.cost, finalpop))

                rx_driver = driver if isinstance(driver, DriverRx) else DriverRxWrapper(driver)

                rx_driver.steps() \
                    .map(get_budget_stage) \
                    .subscribe(lambda proxy_data: process_proxy(*proxy_data))

                driver.max_budget = budgets[-1]

                budget_run = BudgetRun(budgets[-1])
                budget_run.start(rx_driver)
            else:
                e = NotImplementedError()
                logger.exception("Oops. The driver type is not recognized, got %s", show_partial(driver), exc_info=e)
                raise e

        return results, proc_time[-1]

    except NotViableConfiguration as e:
        reason = inspect.trace()[-1]
        logger.info("Configuartion disabled by %s:%d:%s. args:%s", reason[1], reason[2], reason[3], args)
        logger.debug("Configuration disabled args:%s. Stack:", exc_info=e)

    except Exception as e:
        logger.exception("Some error", exc_info=e)

    finally:
        logger.debug("Finished processing. args:%s", args)


def prepare(algo, problem, driver=None, all_drivers=None, driver_pos=0):
    logger = logging.getLogger(__name__)
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
        logger.debug("config: %s", show_conf(config))

        ################################################################################
        # CUSTOMS FOR PROBLEM
        update = {"dims": problem_mod.dims, "fitnesses": problem_mod.fitnesses}
        logger.debug("Per-problem config: %s", update)
        config.update(update)
        logger.debug("config: %s", show_conf(config))

        ################################################################################
        descr = "DRIVER ASSIGNMENT"
        if driver:
            update = {"driver": driver}
            config.update(update)
            logger.debug("%s : %s", descr, driver)
            config.update(update)
            logger.debug("config: %s", show_conf(config))

        ################################################################################
        descr = "CUSTOMS FOR ALGORITHM"
        # example key: SPEA2
        # example key: HGS
        # example key: IMGA
        with suppress(KeyError):
            key = algo
            logger.debug("Try algo_base[%s]", key)
            update = run_config.algo_base[key]
            logger.debug("%s %s: %s: %s",
                         descr,
                         "| by algo dict key:", key, ', '.join(update))
            config.update(update)
            logger.debug("config: %s", show_conf(config))

        ################################################################################
        descr = "CUSTOMS FOR ALGORITHM + SUBDRIVERS"
        # example key: (SPEA2, ()          )
        # example key: (HGS,   (SPEA2)     )
        # example key: (IMGA,  (HGS, SPEA2))
        with suppress(KeyError):
            key = (algo,
                   tuple(all_drivers[driver_pos + 1:])
                   )
            logger.debug("Try algo_base[%s]", key)
            update = run_config.algo_base[key]
            logger.debug("%s %s %s %s: %s %s",
                         descr,
                         "| by algo dict key:", key, "\n    <<", ', '.join(update),
                         update)
            config.update(update)
            logger.debug("config: %s", show_conf(config))

        ################################################################################
        descr = "CUSTOMS FOR PARENTS + ALGORITHM"
        # example key: ((IMGA, HGS), SPEA2)
        # example key: ((IMGA,),     HGS  )
        # example key: ((),          IMGA )
        with suppress(KeyError):
            key = (tuple(all_drivers[:driver_pos]),
                   algo
                   )
            logger.debug("Try algo_base[%s]", key)
            update = run_config.algo_base[key]
            logger.debug("%s %s %s %s: %s %s",
                         descr,
                         "| by algo dict key:", key, "\n    <<", ', '.join(update),
                         update)
            config.update(update)
            logger.debug("config: %s", show_conf(config))

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
            logger.debug("Try algo_base[%s]", key)
            update = run_config.algo_base[key]
            logger.debug("%s %s %s %s: %s %s",
                         descr,
                         "| by algo dict key:", key, "\n    <<", ', '.join(update),
                         update)
            config.update(update)
            logger.debug("config: %s", show_conf(config))

        ################################################################################
        descr = "CUSTOMS (simpl)"
        # example key: (SPEA2, ackley)
        # example key: (SPEA2, zdt1)
        # example key: (HGS, ackley)
        # example key: (HGS, zdt1)
        # example key: (IMGA, ackley)
        # example key: (IMGA, zdt1)
        with suppress(KeyError):
            key = (algo,
                   problem
                   )
            logger.debug("Try cust_base[%s]", key)
            update = run_config.cust_base[key]
            logger.debug("%s %s %s %s: %s %s",
                         descr,
                         "| by cust dict key:", key, "\n    <<", ', '.join(update),
                         update)
            config.update(update)
            logger.debug("config: %s", show_conf(config))

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
            logger.debug("Try cust_base[%s]", key)
            update = run_config.cust_base[key]
            logger.debug("%s %s %s %s: %s %s",
                         descr,
                         "| by cust dict key:", key, "\n    <<", ', '.join(update),
                         update)
            config.update(update)
            logger.debug("config: %s", show_conf(config))

        ################################################################################
        descr = "CUSTOMS FOR ALGORITHM"
        # example fun: init_alg___SPEA2
        # example fun: init_alg___HGS
        # example fun: init_alg___IMGA
        with suppress(AttributeError):
            key = "init_alg___" + algo
            logger.debug("Try %s(…)", key)
            updater = getattr(run_config, key)
            logger.debug("%s %s: %s: %s",
                         descr,
                         "| by algo fun:",
                         key,
                         updater
                         )
            updater(config, problem_mod)
            logger.debug("config: %s", show_conf(config))

        ################################################################################
        descr = "CUSTOMS FOR ALGORITHM + SUBDRIVERS"
        # example fun: init_alg___HGS__SPEA2
        # example fun: init_alg___IMGA__HGS_SPEA2
        with suppress(AttributeError):
            key = "init_alg___" + algo + '__' + '_'.join(all_drivers[driver_pos + 1:])
            logger.debug("Try %s(…)", key)
            updater = getattr(run_config, key)
            logger.debug("%s %s: %s: %s",
                         descr,
                         "| by algo fun:",
                         key,
                         updater
                         )
            updater(config, problem_mod)
            logger.debug("config: %s", show_conf(config))

        ################################################################################
        descr = "CUSTOMS FOR PARENTS + ALGORITHM"
        # example fun: init_alg_IMGA_HGS___SPEA2
        # example fun: init_alg_IMGA___HGS
        with suppress(AttributeError):
            key = "init_alg_" + '_'.join(all_drivers[:driver_pos]) + '___' + algo
            logger.debug("Try %s(…)", key)
            updater = getattr(run_config, key)
            logger.debug("%s %s: %s: %s",
                         descr,
                         "| by algo fun:",
                         key,
                         updater
                         )
            updater(config, problem_mod)
            logger.debug("config: %s", show_conf(config))

        ################################################################################
        descr = "CUSTOMS FOR PARENTS + ALGORITHM + SUBDRIVERS"
        # example fun: init_alg_IMGA___HGS__SPEA2
        with suppress(AttributeError):
            key = "init_alg_" + '_'.join(all_drivers[:driver_pos]) + '___' + algo + '__' + '_'.join(
                all_drivers[driver_pos + 1:])
            logger.debug("Try %s(…)", key)
            updater = getattr(run_config, key)
            logger.debug("%s %s: %s: %s",
                         descr,
                         "| by algo fun:",
                         key,
                         updater
                         )
            updater(config, problem_mod)
            logger.debug("config: %s", show_conf(config))

        ################################################################################
        descr = "CUSTOMS FOR PROBLEM"
        # example key: ackley
        # example key: zdt1
        with suppress(KeyError):
            key = problem
            logger.debug("Try prob_base[%s]", key)
            update = run_config.prob_base[key]
            logger.debug("%s %s: %s",
                         descr,
                         "| by prob dict key:", key, "\n    <<", ', '.join(run_config.prob_base[key]),
                         update)
            config.update(update)
            logger.debug("config: %s", show_conf(config))

        ################################################################################
        descr = "CUSTOMS FOR PROBLEM"
        # example fun: init_prob____ackley
        with suppress(AttributeError):
            key = "init_prob____" + problem
            logger.debug("Try %s(…)", key)
            updater = getattr(run_config, key)
            logger.debug("%s %s: %s: %s",
                         descr,
                         "| by prob fun:",
                         key,
                         updater
                         )
            updater(config, problem_mod)
            logger.debug("config: %s", show_conf(config))

        ################################################################################
        descr = "CUSTOMS"
        # example fun: init_cust___SPEA2____ackley  # configure SPEA2 for ackley
        # example fun: init_cust___SPEA2____zdt1
        # example fun: init_cust_IMGA_HGS___SPEA2____ackley  # configure SPEA2 for ackley when under IMGA+HGS
        # example fun: init_cust_IMGA_HGS___SPEA2____zdt1
        # example fun: init_cust_IMGA___HGS__SPEA2____ackley  # configure HGS for ackley when under IMGA w/ SPEA2 driver
        # example fun: init_cust_IMGA___HGS__SPEA2____zdt1
        # example fun: init_cust___IMGA__HGS_SPEA2____ackley  # configure IMGA for ackley w/ HGS+SPEA2 driver
        # example fun: init_cust___IMGA__HGS_SPEA2____zdt1
        with suppress(AttributeError):
            overdriver = ''.join('_' + x for x in all_drivers[:driver_pos])
            algo_pref = "___" + algo
            subdrivers = ""
            if all_drivers[driver_pos + 1:]:
                subdrivers = "__" + '_'.join(all_drivers[driver_pos + 1:])
            problem_suf = "____" + problem
            key = "init_cust" + overdriver + algo_pref + subdrivers + problem_suf
            logger.debug("Try %s(…)", key)
            updater = getattr(run_config, key)
            logger.debug("%s %s: %s: %s",
                         descr,
                         "| by cust fun:",
                         key,
                         updater
                         )
            updater(config, problem_mod)
            logger.debug("config: %s", show_conf(config))

        ################################################################################
        descr = "GENERATING POPULATION"
        if "population" not in config:
            initial_population = gen_population(64, problem_mod.dims)
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
