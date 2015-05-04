# base 
import multiprocessing
import time
import unittest
import sys
import collections
import operator


def run_parallel(args):
    order = [ ('ZDT6', 'hgs_nsga2' ),
              ('ZDT4', 'hgs_nsga2' ),
              ('ZDT4', 'imga_nsga2'),
              ('ZDT3', 'hgs_nsga2' ),
              ('ZDT1', 'hgs_nsga2' ),
              ('ZDT2', 'hgs_nsga2' ),
              ('ZDT4', 'nsga2'     ),
              ('ZDT6', 'nsga2'     ),
              ('kursawe',  'hgs_nsga2' ),
              ('ZDT3', 'nsga2'     ),
              ('ZDT1', 'nsga2'     ),
              ('ZDT2', 'nsga2'     ),
              ('ZDT6', 'imga_nsga2'),
              ('ZDT3', 'imga_nsga2'),
              ('ZDT2', 'imga_nsga2'),
              ('ZDT1', 'imga_nsga2'),
              ('ZDT2', 'hgs_spea2' ),
              ('ZDT1', 'hgs_spea2' ),
              ('kursawe',  'imga_nsga2'),
              ('kursawe',  'nsga2'     ),
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
              ('ackley',   'imga_nsga2'),
              ('ackley',   'hgs_nsga2' ),
              ('ZDT4', 'spea2'     ),
              ('ZDT1', 'spea2'     ),
              ('ZDT6', 'spea2'     ),
              ('ZDT2', 'spea2'     ),
              ('ZDT3', 'spea2'     ),
              ('ackley',   'nsga2'     ),
              ('ZDT6', 'hgs_ibea'  ),
              ('ackley',   'imga_spea2'),
              ('ackley',   'hgs_spea2' ),
              ('ackley',   'spea2'     ),
              ('ackley',   'imga_ibea' ),
              ('ackley',   'ibea'      ),
              ('ackley',   'hgs_ibea'  ),
              ('parabol',  'hgs_spea2' ),
              ('parabol',  'hgs_ibea'  ),
              ('parabol',  'hgs_nsga2' )
            ]

    if args['--algo']:
        algos = args['--algo'].split(',')
        order = [ (problem, algo)
                  for problem, algo
                  in order
                  if algo in algos
                ]

    if args['--problem']:
        problems = args['--problem'].split(',')
        order = [ (problem, algo)
                  for problem, algo
                  in order
                  if problem in problems
                ]

    order = order * int(args['-N'])

    print("Running following tests:")
    for problem, algo in order:
        print("  {problem:12} :: {algo:12}".format(**locals()))
    p = multiprocessing.Pool(int(args['-j']))

    wall_time = -time.perf_counter()
    results = p.map(run_parallel__f, order)
    wall_time += time.perf_counter()

    proc_times = sum(results)
    speedup = proc_times / wall_time
    
    print("wall time:           {wall_time:7.3f} s\n"\
          "CPU+user time:       {proc_times:7.3f}s\n"\
          "est. speedup calc.:  {speedup:7.3f}x"
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

def run_parallel__f(args):
    problem, algo = args
    module_name = '.'.join(['problems', problem, algo, 'run'])
    
    proc_time = -time.process_time()
    unittest.main(module=module_name, exit=False, argv=[sys.argv[0]])
    proc_time += time.process_time()
    
    return proc_time
