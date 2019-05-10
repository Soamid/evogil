import collections
import logging
import operator
import random
from datetime import datetime

import rx
from rx import operators as ops

from evotools import rxtools
from simulation import factory, worker
from simulation.timing import log_time
from simulation.timing import system_time

logger = logging.getLogger(__name__)


def run_parallel(args, worker_factory):
    simulation_cases = worker_factory(args)

    logger.debug("Shuffling the job queue")
    random.shuffle(simulation_cases)

    logger.debug("Creating the pool")

    processes_no = int(args["-j"])
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
            ops.map(lambda i: worker.BudgetWorker(simulation_cases[i], i)),
            ops.flat_map(lambda w: rxtools.from_process(w.run)),
        ).pipe(ops.do_action(on_next=process_result)).run()
    log_summary(args, results, simulation_cases, wall_time)
    rxtools.shutdown_default_executor()


def log_simulation_stats(start_time, simulation_id, simultations_count):
    current_time = datetime.now()
    diff_time = current_time - start_time
    ratio = simulation_id * 1.0 / simultations_count
    try:
        est_delivery_time = start_time + diff_time / ratio
        time_to_delivery = est_delivery_time - current_time
        logging.info(
            "Job queue progress: %.3f%%. Est. finish in %02d:%02d:%02d (at %s)",
            ratio * 100,
            time_to_delivery.days * 24 + time_to_delivery.seconds // 3600,
            time_to_delivery.seconds // 60,
            time_to_delivery.seconds % 60,
            est_delivery_time.strftime("%Y-%m-%d %H:%M:%S.%f"),
        )
    except ZeroDivisionError:
        logging.info("Job queue progress: %.3f%%. Est. finish: unknown yet", ratio)


def log_summary(args, results, simulation_cases, wall_time):
    proc_times = sum(subres[1] for subres in results if subres is not None)
    errors = [
        (simulation.config, simulation.run_id)
        for comp_result, simulation in zip(results, simulation_cases)
        if comp_result is None
    ]
    speedup = proc_times / wall_time[0]
    logger.info("SUMMARY:")
    logger.info("  wall time:     %7.3f", wall_time[0])
    logger.info("  CPU+user time: %7.3f", proc_times)
    logger.info("  est. speedup:  %7.3f", speedup)
    if errors:
        logger.error("Errors encountered:")
        for (probl, algo), runid in errors:
            logger.error(
                "  %9s :: %14s :: runID=%d ",
                probl,
                algo,
                runid
            )
    summary = collections.defaultdict(float)
    for simulation, subres in zip(simulation_cases, results):
        if subres:
            summary[simulation.config] += subres[1]
    if logger.isEnabledFor(logging.INFO):
        logger.info("Running time:")
        res = []
        for (prob, alg), timesum in sorted(
            summary.items(), key=operator.itemgetter(1), reverse=True
        ):
            prob_show = "'" + prob + "'"
            alg_show = "'" + alg + "'"
            avg_time = timesum / float(args["-N"])
            logger.debug(
                "  prob:{prob_show:16} algo:{alg_show:16}) time:{avg_time:>8.3f}s".format(
                    **locals()
                )
            )
