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

from functools import partial


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
    algo = 'IBEA'
    problem = 'ackley'
    budget = 500

    drivers = algo.split('+')

    final_driver = None
    for driver_pos, driver in list(enumerate(drivers))[::-1]:
        final_driver = prepare(driver,
                               problem,
                               final_driver,
                               drivers, driver_pos
                              )

    gen = final_driver().steps()

    total_cost, result = 0, None
    proc_time = -time.process_time()
    # while total_cost <= budget:
    #     cost, result = next(gen)
    #     total_cost += cost
    #     print("RESULT:", cost, total_cost, result)
    proc_time += time.process_time()
    
    return proc_time

def prepare(algo,
            problem,
            driver=None,
            all_drivers=[], driver_pos=0
           ):

    algo_mod   = '.'.join(['algorithms', algo, algo])
    algo_mod   = import_module(algo_mod)
    algo_class = getattr(algo_mod, algo)

    problem_mod = '.'.join(['problems', problem, 'problem'])
    problem_mod = import_module(problem_mod)


    # START WITH META-CONFIG
    algo_config = {
        "__metaconfig__populationsize": 10,
    }

    ################################################################################
    # CUSTOMS FOR PROBLEM
    algo_config.update({
        "dims":       problem_mod.dims,
        "fitnesses":  problem_mod.fitnesses
    })
    
    ################################################################################
    descr = "CUSTOMS FOR ALGORITHM"
    # example key: SPEA2
    # example key: HGS
    # example key: IMGA
    with suppress(KeyError):
        key = algo
        algo_config.update( run_config.options_base[ key ] )
        print(descr, "| by dict key:", key)
    
    ################################################################################
    descr = "CUSTOMS FOR ALGORITHM + SUBDRIVERS"
    # example key: (SPEA2, ()          )
    # example key: (HGS,   (SPEA2)     )
    # example key: (IMGA,  (HGS, SPEA2))
    with suppress(KeyError):
        key = (algo,
               tuple(all_drivers[driver_pos+1:])
              )
        algo_config.update( run_config.options_base[ key ] )
        print(descr, "| by dict key:", key)

    ################################################################################
    descr = "CUSTOMS FOR PARENTS + ALGORITHM"
    # example key: ((IMGA, HGS), SPEA2)
    # example key: ((IMGA),      HGS  )
    # example key: ((),          IMGA )
    with suppress(KeyError):
        key = (tuple(all_drivers[:max(0,driver_pos-1)]),
               algo
              )
        algo_config.update( run_config.options_base[ key ] )
        print(descr, "| by dict key:", key)

    ################################################################################
    descr = "CUSTOMS FOR PARENTS + ALGORITHM + SUBDRIVERS"
    # example key: ((IMGA, HGS), SPEA2, ()          )
    # example key: ((IMGA),      HGS,   (SPEA2)     )
    # example key: ((),          IMGA,  (HGS, SPEA2))
    with suppress(KeyError):
        key = (tuple(all_drivers[:max(0,driver_pos-1)]),
               algo,
               tuple(all_drivers[driver_pos+1:])
              )
        algo_config.update( run_config.options_base[ key ] )
        print(descr, "| by dict key:", key)
    

    ################################################################################
    descr = "CUSTOMS FOR ALGORITHM"
    # example fun: init_SPEA2
    # example fun: init_HGS
    # example fun: init_IMGA
    with suppress(AttributeError):
        key = "init_" + algo
        getattr(run_config, key)(algo_config, problem_mod)
        print(descr, "| by fun:", key)
    
    ################################################################################
    descr = "CUSTOMS FOR ALGORITHM + SUBDRIVERS"
    # example fun: init_HGS__SPEA2
    # example fun: init_IMGA__HGS_SPEA2
    with suppress(AttributeError):
        key = "init_" + algo + '__' + '_'.join(all_drivers[driver_pos+1:])
        getattr(run_config, key)(algo_config, problem_mod)
        print(descr, "| by fun:", key)
    
    ################################################################################
    descr = "CUSTOMS FOR PARENTS + ALGORITHM"
    # example fun: init_IMGA_HGS__SPEA2
    # example fun: init_IMGA__HGS
    with suppress(AttributeError):
        key = "init_" + '_'.join(all_drivers[:max(0,driver_pos-1)]) + '__' + algo
        getattr(run_config, key)(algo_config, problem_mod)
        print(descr, "| by fun:", key)
    
    ################################################################################
    descr = "CUSTOMS FOR PARENTS + ALGORITHM + SUBDRIVERS"
    # example fun: init_IMGA__HGS__SPEA2
    with suppress(AttributeError):
        key = "init_" + '_'.join(all_drivers[:max(0,driver_pos-1)]) + '__' + algo + '__' + '_'.join(all_drivers[driver_pos+1:])
        getattr(run_config, key)(algo_config, problem_mod)
        print(descr, "| by fun:", key)
    
    ################################################################################
    descr = "GENERATING POPULATION"
    if "population" not in algo_config:
        algo_config.update({
            "population": gen_population(algo_config["__metaconfig__populationsize"],
                                         problem_mod.dims
                                        )
        })
        print(descr)

    ################################################################################
    # DROPPING TRASH
    algo_config = { k: v
                    for k, v
                    in algo_config.items()
                    if not k.startswith('__metaconfig__')
                  }


    print_dict = algo_config.copy()
    del print_dict["population"]
    print("algo:", algo, "algos:", all_drivers[driver_pos:], "problem:", problem, "with sub-driver:", driver, "all_drivers:", all_drivers, "driver_pos:", driver_pos)
    print(print_dict)

    try:
        algo_class(**algo_config)
    except Exception as e:
        print("ERR!")
        raise e
    
    print("OKAY")

    return partial(algo_class, **algo_config)

