import collections
import inspect
import logging
import operator
import os
import random
import time
from datetime import datetime

import rx
from rx import operators as ops

from algorithms.base.driver import BudgetRun
from evotools import rxtools
from simulation import factory, log_helper
from simulation.run_config import NotViableConfiguration
from simulation.serialization import RunResult
from simulation.timing import log_time, process_time
from simulation.timing import system_time

logger = logging.getLogger(__name__)


def run_parallel(args):
    simulation_cases = factory.create_simulation(args)

    logger.debug("Shuffling the job queue")
    random.shuffle(simulation_cases)

    logger.debug("Creating the pool")

    processes_no = int(args['-j'])
    rxtools.configure_default_executor(processes_no)

    wall_time = []
    start_time = datetime.now()
    results = []
    logger.debug("Simulation cases: %s", simulation_cases)
    logger.debug("Work will be divided into %d processes", processes_no)

    with log_time(system_time, logger, "Pool evaluated in {time_res}s", out=wall_time):
        def process_result(subres):
            results.append(subres)
            log_simulation_stats(start_time, subres[-1], len(simulation_cases))

        rx.from_iterable(range(len(simulation_cases))).pipe(
            ops.flat_map(lambda i: rxtools.from_process(worker, simulation_cases[i], i))
        ).pipe(
            ops.do_action(on_next=process_result)
        ).run()
    log_summary(args, results, simulation_cases, wall_time)
    rxtools.shutdown_default_executor()


def log_simulation_stats(start_time, simulation_id, simultations_count):
    current_time = datetime.now()
    diff_time = current_time - start_time
    ratio = simulation_id * 1. / simultations_count
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


def log_summary(args, results, simulation_cases, wall_time):
    proc_times = sum(subres[1]
                     for subres
                     in results
                     if subres is not None)
    errors = [(simulation.config, simulation.budgets, simulation.run_id)
              for comp_result, simulation
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
    for simulation, subres in zip(simulation_cases, results):
        if subres:
            summary[simulation.config] += subres[1]
    if logger.isEnabledFor(logging.INFO):
        logger.info("Running time:")
        res = []
        for (prob, alg), timesum in sorted(summary.items(),
                                           key=operator.itemgetter(1),
                                           reverse=True):
            prob_show = "'" + prob + "'"
            alg_show = "'" + alg + "'"
            avg_time = timesum / float(args['-N'])
            logger.debug("  prob:{prob_show:16} algo:{alg_show:16}) time:{avg_time:>8.3f}s".format(**locals()))


def worker(simulation, simulation_id):
    log_helper.init()
    logger = logging.getLogger(__name__)
    logger.debug("Starting the worker. PID: %d, simulation case: %s", os.getpid(), simulation)

    if simulation.renice:
        logger.debug("Renice the process PID:%s by %s", os.getpid(), simulation)
        os.nice(int(simulation.renice))

    logger.debug("Getting random seed")
    # basically we duplicate the code of https://github.com/python/cpython/blob/master/Lib/random.py#L111 because
    # in case os.urandom is not available, random.seed defaults to epoch time. That would set the seed equal in each
    # process, which is not acceptable.
    try:
        random_seed = int.from_bytes(os.urandom(2500), 'big')
    except NotImplementedError:
        random_seed = int(time.time() * 256 + os.getpid())  # that's not enough for MT, but will have to do for now.
    random.seed(random_seed)

    runres = RunResult(simulation)

    try:
        final_driver, problem_mod = factory.prepare(simulation.algorithm_name, simulation.problem_name)

        logger.debug("Creating the driver used to perform computation")

        driver = final_driver()
        total_cost, result = 0, None

        proc_time = []
        results = []

        logger.debug("Beginning processing of %s, simulation: %s", driver, simulation)
        with log_time(process_time, logger, "Processing done in {time_res}s CPU time", out=proc_time):
            def process_results(budget: int):
                finalpop = driver.finalized_population()
                finalpop_fit = [[fit(x) for fit in problem_mod.fitnesses] for x in finalpop]
                runres.store(budget, driver.cost, finalpop, finalpop_fit)
                results.append((driver.cost, finalpop))

            driver.max_budget = simulation.budgets[-1]

            for budget in simulation.budgets:
                budget_run = BudgetRun(budget)
                budget_run.create_job(driver).pipe(
                    ops.do_action(on_completed=lambda: process_results(budget))
                ).subscribe(lambda proxy: logger.debug(
                    "{}{} : Driver progress: budget={}, current cost={}, driver step={}".format(
                        simulation.algorithm_name, simulation.problem_name, budget, proxy.cost,
                        proxy.step_no)))


        return results, proc_time[-1], simulation_id

    except NotViableConfiguration as e:
        reason = inspect.trace()[-1]
        logger.info("Configuartion disabled by %s:%d:%s. simulation case:%s", reason[1], reason[2], reason[3],
                    simulation)
        logger.debug("Configuration disabled args:%s. Stack:", exc_info=e)

    except Exception as e:
        logger.exception("Some error", exc_info=e)

    finally:
        logger.debug("Finished processing. simulation case:%s", simulation)
