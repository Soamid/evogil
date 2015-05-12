# base 
import multiprocessing
import time
# import unittest
import sys
import collections
import operator

from importlib import import_module
from contextlib import suppress

from evotools.ea_utils import gen_population
from evotools import run_config


def run_parallel(args):
    order = [ 
              # ('ZDT6', 'hgs_nsga2' ),
              # ('ZDT4', 'hgs_nsga2' ),
              # ('ZDT4', 'imga_nsga2'),
              # ('ZDT3', 'hgs_nsga2' ),
              # ('ZDT1', 'hgs_nsga2' ),
              # ('ZDT2', 'hgs_nsga2' ),
              # ('ZDT4', 'nsga2'     ),
              # ('ZDT6', 'nsga2'     ),
              # ('kursawe',  'hgs_nsga2' ),
              # ('ZDT3', 'nsga2'     ),
              # ('ZDT1', 'nsga2'     ),
              # ('ZDT2', 'nsga2'     ),
              # ('ZDT6', 'imga_nsga2'),
              # ('ZDT3', 'imga_nsga2'),
              # ('ZDT2', 'imga_nsga2'),
              # ('ZDT1', 'imga_nsga2'),
              ('ZDT2', 'hgs_spea2' ),
              ('ZDT1', 'hgs_spea2' ),
              # ('kursawe',  'imga_nsga2'),
              # ('kursawe',  'nsga2'     ),
              ('ZDT4', 'hgs_spea2' ),
              ('ZDT4', 'ibea'      ),
              ('ZDT4', 'imga_ibea' ),
              ('kursawe',  'ibea'      ),
              ('kursawe',  'imga_ibea' ),
              ('kursawe',  'spea2'     ),
              ('kursawe',  'imga_spea2'),
              ('ZDT6', 'ibea'      ),
              ('ZDT6', 'imga_ibea' ),
              ('kursawe',  'hgs_spea2' ),
              ('ZDT3', 'hgs_spea2' ),
              ('ZDT3', 'ibea'      ),
              ('ZDT3', 'imga_ibea' ),
              ('ZDT4', 'imga_spea2'),
              ('ZDT2', 'imga_ibea' ),
              ('ZDT2', 'ibea'      ),
              ('ZDT1', 'ibea'      ),
              ('kursawe',  'hgs_ibea'  ),
              ('ZDT1', 'imga_ibea' ),
              ('ZDT4', 'hgs_ibea'  ),
              ('ZDT6', 'hgs_spea2' ),
              ('ZDT3', 'hgs_ibea'  ),
              ('ZDT1', 'hgs_ibea'  ),
              ('ZDT2', 'hgs_ibea'  ),
              ('ZDT1', 'imga_spea2'),
              ('ZDT2', 'imga_spea2'),
              ('ZDT3', 'imga_spea2'),
              ('ZDT6', 'imga_spea2'),
              # ('ackley',   'imga_nsga2'),
              # ('ackley',   'hgs_nsga2' ),
              ('ZDT4', 'spea2'     ),
              ('ZDT1', 'spea2'     ),
              ('ZDT6', 'spea2'     ),
              ('ZDT2', 'spea2'     ),
              ('ZDT3', 'spea2'     ),
              # ('ackley',   'nsga2'     ),
              ('ZDT6', 'hgs_ibea'  ),
              ('ackley',   'imga_spea2'),
              ('ackley',   'hgs_spea2' ),
              ('ackley',   'spea2'     ),
              ('ackley',   'imga_ibea' ),
              ('ackley',   'ibea'      ),
              ('ackley',   'hgs_ibea'  ),
              ('parabol',  'hgs_spea2' ),
              ('parabol',  'hgs_ibea'  )
              # ('parabol',  'hgs_nsga2' )
            ]

    if args['--algo']:
        algos = args['--algo'].lower().split(',')
        order = [ (problem, algo)
                  for problem, algo
                  in order
                  if algo.lower() in algos
                ]

    if args['--problem']:
        problems = args['--problem'].lower().split(',')
        order = [ (problem, algo)
                  for problem, algo
                  in order
                  if problem.lower() in problems
                ]

    print("Selected following tests:")
    for problem, algo in order:
        print("  {problem:12} :: {algo:12}".format(**locals()))

    order = [ test
              for test in order
              for i in range(int(args['-N']))
            ]
    order = [('ackley',   'ibea')] # TODO [kgdk]: REMOVE ME


    p = multiprocessing.Pool(int(args['-j']))

    wall_time = -time.perf_counter()
    results = p.map(worker, order)
    wall_time += time.perf_counter()

    proc_times = sum(results)
    speedup = proc_times / wall_time
    
    print("wall time:     {wall_time:7.3f} s\n"\
          "CPU+user time: {proc_times:7.3f}s\n"\
          "est. speedup:  {speedup:7.3f}x"
          .format(**locals()))

    summary = collections.defaultdict(float)
    for bench, res in zip(order, results):
        summary[bench] += res


    print("Running time list:")
    for (prob, alg), timesum in sorted(summary.items(),
                                       key=operator.itemgetter(1),
                                       reverse=True):
        prob_show = "'" + prob + "'"
        alg_show = "'" + alg + "'"
        avg_time = timesum / float(args['-N'])
        print("  ({prob_show:16}, {alg_show:16}),  # {avg_time:7.3f}s".format(**locals()))


def worker(args):
    #problem, algo = args # TODO [kgdk]
    # module_name = '.'.join(['problems', problem, algo, 'run'])
    algo = 'IBEA'
    problem = 'ackley'
    budget = 500

    problem_mod = '.'.join(['problems', problem, 'problem'])
    problem_mod = import_module(problem_mod)

    algo_mod = '.'.join(['algorithms', algo, algo])
    algo_mod = import_module(algo_mod)

    algo_class = getattr(algo_mod, algo)


    # empty config
    algo_config = {
        "__metaconfig__populationsize": 10,
    }

    # take base config
    with suppress(KeyError):
        algo_config.update(run_config.options_base[algo])
    
    # set some common params
    algo_config.update({
        "population": gen_population(40, problem_mod.dims),
        "dims": problem_mod.dims,
        "fitnesses": problem_mod.fitnesses
    })
    
    # custom, per problem params
    with suppress(AttributeError):
        getattr(run_config, "init_" + problem)(algo_config, problem_mod)
    
    # custom, per algorithm params
    with suppress(AttributeError):
        getattr(run_config, "init_" + algo)(algo_config, problem_mod)
    
    # custom, per problem+algorithm params
    with suppress(AttributeError):
        getattr(run_config, "init_" + algo + "_" + problem)(algo_config, problem_mod)
    
    # drop trashy arguments
    algo_config = { k: v
                    for k, v
                    in algo_config.items()
                    if not k.startswith('__metaconfig__')
                  }

    print("THE CONFIG")
    print(algo_config)

    gen = algo_class(**algo_config).steps()
    total_cost, result = 0, None

    proc_time = -time.process_time()
    while total_cost <= budget:
        cost, result = next(gen)
        total_cost += cost
        print("RESULT:", cost, total_cost, result)
    proc_time += time.process_time()
    
    return proc_time

