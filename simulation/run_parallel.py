import collections
import inspect
import logging
import multiprocessing
import operator
import os
import random
import time
from datetime import datetime

from algorithms.base.drivergen import Driver, BudgetRun
from evotools.ea_utils import gen_population
from evotools.random_tools import show_partial, close_and_join
from simulation import factory
from simulation.run_config import NotViableConfiguration
from simulation.serialization import RunResult, RESULTS_DIR
from simulation.timing import log_time, process_time
from simulation.timing import system_time

logger = logging.getLogger(__name__)


def run_parallel(args, queue):
    simulation_cases = factory.create_simulation(args)

    logger.debug("Shuffling the job queue")
    random.shuffle(simulation_cases)

    logger.debug("Creating the pool")

    with close_and_join(multiprocessing.Pool(int(args['-j']))) as p:

        wall_time = []
        start_time = datetime.now()
        results = []
        with log_time(system_time, logger, "Pool evaluated in {time_res}s", out=wall_time):
            for i, subres in enumerate(p.imap(worker, simulation_cases, chunksize=1)):
                results.append(subres)

                current_time = datetime.now()
                diff_time = current_time - start_time
                ratio = i * 1. / len(simulation_cases)
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
              in zip(results, simulation_cases)
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
    for (bench, _, _, _), subres in zip(simulation_cases, results):
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
            final_driver, problem_mod = factory.prepare(driver,
                                                        problem,
                                                        final_driver,
                                                        drivers, driver_pos
                                                        )

        logger.debug("Creating the driver used to perform computation")

        population = final_driver.keywords["population"] if "population" not in final_driver.keywords \
            else gen_population(64, problem_mod.dims)

        driver = final_driver(population=population)
        total_cost, result = 0, None

        proc_time = []
        results = []

        logger.debug("Beginning processing of %s, args: %s", driver, args)
        with log_time(process_time, logger, "Processing done in {time_res}s CPU time", out=proc_time):
            if isinstance(driver, Driver):
                def process_results(budget: int):
                    finalpop = driver.finalized_population()
                    finalpop_fit = [[fit(x) for fit in problem_mod.fitnesses] for x in finalpop]
                    runres.store(budget, driver.cost, finalpop, finalpop_fit)
                    results.append((driver.cost, finalpop))

                driver.max_budget = budgets[-1]

                for budget in budgets:
                    budget_run = BudgetRun(budget)
                    budget_run.create_job(driver) \
                        .do_action(on_completed=lambda: process_results(budget)) \
                        .subscribe(lambda proxy: print(
                        "Driver progress: budget={}, current cost={}, driver step={}".format(budget, proxy.cost,
                                                                                             proxy.step_no)))
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
