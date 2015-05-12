#!/usr/bin/env python3
"""EvoGIL helper.

Usage:
  evogil.py -h | --help 
  evogil.py run [options]
  evogil.py summary
  evogil.py (stats | statistics) [options]
  evogil.py pictures [options]
  evogil.py best_fronts [options]

In future possibly we could get those commands working:
  evogil.py violin [options]
  evogil.py plotter [options]

Commands:
  run
    Performs benchmarks.
  summary
    Returns number of results for each (algorithm,problem,budget)
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
        Only for selected algorithms(s) separated by comma. List available
        below in "Algorithms" section.
  -p <problem_name>, --problem <problem_name>
        Only for selected problem(s) separated by comma. List available
        below in "Problems" section.
  -b <bootstrap-iter>, --bootstrap <bootstrap-iter>
        Bootstrap iterations.
        [default: 10000]
  -j <jobs>
        Number of processes to spawn.
        [default: 4]
  -N <iterations>
        Repeat N times.
        [default: 1]

Algorithms:
  hgs_ibea
  hgs_nsga2
  hgs_spea2
  ibea
  imga_ibea
  imga_nsga2
  imga_spea2
  nsga2
  spea2

Problems:
  ZDT1
  ZDT2
  ZDT3
  ZDT4
  ZDT6
  ackley
  kursawe
  parabol
"""

# docopt
from docopt import docopt

# self
import evotools.stats
import evotools.violin
import evotools.run_parallel
import evotools.benchmark_results
import evotools.pictures
import evotools.best_fronts


if __name__ == '__main__':
    argv = docopt(__doc__, version='EvoGIL 3.0')

    if argv['run']:
        evotools.run_parallel.run_parallel(argv)
    elif argv['statistics'] or argv['stats']:
        evotools.stats.statistics(argv)
    elif argv['pictures']:
        evotools.pictures.pictures_from_stats(argv)
    elif argv['best_fronts']:
        evotools.best_fronts.main()
    # elif argv['violin']:
    #     evotools.violin.violin(argv)
    elif argv['summary']:
        evotools.benchmark_results.analyse_results()

