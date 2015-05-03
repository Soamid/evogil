#!/usr/bin/env python3
"""EvoGIL helper.

Usage:
  evogil.py -h | --help 
  evogil.py violin [options]
  evogil.py (stats | statistics) [options]
  evogil.py pictures_from_stats_new [options]
  evogil.py run_parallel [options]

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
  ackley
  coemoa_a (ZDT1)
  coemoa_b (ZDT2)
  coemoa_c (ZDT3)
  coemoa_d (ZDT4)
  coemoa_e (ZDT6)
  kursawe
  parabol
"""


# base
import json
import multiprocessing
import numpy
import os
import pathlib
import random
import sys
import time
import unittest
from contextlib import contextmanager
from functools import reduce
from math import sqrt

# docopt
import docopt

# numpy + matplotlib
from numpy.linalg import LinAlgError
import matplotlib.pyplot as plt

# self
import evotools.stats
import evotools.violin
import evotools.run_parallel

# from ep.utils import ea_utils
# import problems.ackley.problem as ackley
# import problems.coemoa_a.problem as zdt1
# import problems.coemoa_b.problem as zdt2
# import problems.coemoa_c.problem as zdt3
# import problems.coemoa_d.problem as zdt4
# import problems.coemoa_e.problem as zdt6


if __name__ == '__main__':
    argv = docopt.docopt(__doc__, version='EvoGIL 3.0')

    if argv['run_parallel']:
        evotools.run_parallel.run_parallel(argv)
    elif argv['statistics'] or argv['stats']:
        evotools.stats.statistics(argv)
    elif argv['violin']:
        evotools.violin.violin(argv)
    elif argv['pictures_from_stats_new']:
        pictures_from_stats_new(argv)

