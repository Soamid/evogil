#!/usr/bin/env python3
"""EvoGIL helper.

Usage:
  evogil.py -h | --help 
  evogil.py run <budget> [options]
  evogil.py summary
  evogil.py (stats | statistics) [options]
  evogil.py pictures [options]
  evogil.py best_fronts
  evogil.py violin [options]

Commands:
  run
    Performs benchmarks. Param: budget(s), list of integers separated by comma.
  summary
    Returns number of results for each tuple: algorithm, problem, budget.
  stats
    Generates statistics from benchmarks' results.
  pictures
    Some pictures?
  violin
    Plots violin plots?
  results
    Yields some info about performed benchmarks.

Options:
  -a <algo_name>, --algo <algo_name>       
        Only for selected algorithms(s) separated by comma. You can combine
        meta-algorithms with others by joining them with '+', eg.
            HGS+IBEA
            IMGA+SPEA2
            HGS+IMGS+HGS+IMGA+IMGA+IMGA+SPEA2 (this should work as well)
        Available algorithms (list may be out-of-date):
            NSGAII
            SPEA2
            IBEA
        Available meta-algorithms (list may be out-of-date):
            HGS
            IMGA
        [default: HGS+NSGAII,HGS+SPEA2,HGS+IBEA,IBEA+NSGAII,IBEA+SPEA2,IBEA+IBEA,NSGAII,SPEA2,IBEA]
  -p <problem_name>, --problem <problem_name>
        Only for selected problem(s) separated by comma.
        Available problems (list may be out-of-date):
            ZDT1
            ZDT2
            ZDT3
            ZDT4
            ZDT6
            ackley
            kursawe
        [default: ZDT1,ZDT2,ZDT3,ZDT4,ZDT6,ackley,kursawe]
  -b <bootstrap-iter>, --bootstrap <bootstrap-iter>
        Bootstrap iterations.
        [default: 10000]
  -j <jobs>
        Number of processes to spawn.
        [default: 4]
  -N <iterations>
        Repeat N times.
        [default: 1]
"""

# docopt
from docopt import docopt

# self
from evotools.log_helper import get_logger, init_loggers
import evotools.stats
from evotools.timing import system_time, log_time
import evotools.violin
import evotools.run_parallel
import evotools.benchmark_results
import evotools.pictures
import evotools.best_fronts


init_loggers()
logger = get_logger('evogil')


if __name__ == '__main__':
    logger.debug("Starting the evogil. Parsing arguments.")
    with log_time(system_time, logger, "Parsing done in {time_res}s"):
        argv = docopt(__doc__, version='EvoGIL 3.0')
    logger.debug("Parsing result: %s", argv)

    run_dict = {
        'run':         evotools.run_parallel.run_parallel,
        'statistics':  evotools.stats.statistics,
        'stats':       evotools.stats.statistics,
        'pictures':    evotools.pictures.pictures_from_stats,
        'best_fronts': evotools.best_fronts.main,
        'violin':      evotools.violin.violin,
        'summary':     evotools.benchmark_results.analyse_results,
    }

    for k, v in run_dict.items():
        logger.debug("run_dict: k,v = %s,%s", k, v)
        if argv[k]:
            logger.debug("run_dict match. argv[k]=%s", argv[k])
            v(argv)
            break
