# base 
import multiprocessing
import time
import unittest
import sys
import collections
import operator


def run_parallel(args):
    order = [ ('coemoa_e', 'hgs_nsga2' ),
              ('coemoa_d', 'hgs_nsga2' ),
              ('coemoa_d', 'imga_nsga2'),
              ('coemoa_c', 'hgs_nsga2' ),
              ('coemoa_a', 'hgs_nsga2' ),
              ('coemoa_b', 'hgs_nsga2' ),
              ('coemoa_d', 'nsga2'     ),
              ('coemoa_e', 'nsga2'     ),
              ('kursawe',  'hgs_nsga2' ),
              ('coemoa_c', 'nsga2'     ),
              ('coemoa_a', 'nsga2'     ),
              ('coemoa_b', 'nsga2'     ),
              ('coemoa_e', 'imga_nsga2'),
              ('coemoa_c', 'imga_nsga2'),
              ('coemoa_b', 'imga_nsga2'),
              ('coemoa_a', 'imga_nsga2'),
              ('coemoa_b', 'hgs_spea2' ),
              ('coemoa_a', 'hgs_spea2' ),
              ('kursawe',  'imga_nsga2'),
              ('kursawe',  'nsga2'     ),
              ('coemoa_d', 'hgs_spea2' ),
              ('coemoa_d', 'ibea'      ),
              ('coemoa_d', 'imga_ibea' ),
              ('kursawe',  'ibea'      ),
              ('kursawe',  'imga_ibea' ),
              ('kursawe',  'spea2'     ),
              ('kursawe',  'imga_spea2'),
              ('coemoa_e', 'ibea'      ),
              ('coemoa_e', 'imga_ibea' ),
              ('kursawe',  'hgs_spea2' ),
              ('coemoa_c', 'hgs_spea2' ),
              ('coemoa_c', 'ibea'      ),
              ('coemoa_c', 'imga_ibea' ),
              ('coemoa_d', 'imga_spea2'),
              ('coemoa_b', 'imga_ibea' ),
              ('coemoa_b', 'ibea'      ),
              ('coemoa_a', 'ibea'      ),
              ('kursawe',  'hgs_ibea'  ),
              ('coemoa_a', 'imga_ibea' ),
              ('coemoa_d', 'hgs_ibea'  ),
              ('coemoa_e', 'hgs_spea2' ),
              ('coemoa_c', 'hgs_ibea'  ),
              ('coemoa_a', 'hgs_ibea'  ),
              ('coemoa_b', 'hgs_ibea'  ),
              ('coemoa_a', 'imga_spea2'),
              ('coemoa_b', 'imga_spea2'),
              ('coemoa_c', 'imga_spea2'),
              ('coemoa_e', 'imga_spea2'),
              ('ackley',   'imga_nsga2'),
              ('ackley',   'hgs_nsga2' ),
              ('coemoa_d', 'spea2'     ),
              ('coemoa_a', 'spea2'     ),
              ('coemoa_e', 'spea2'     ),
              ('coemoa_b', 'spea2'     ),
              ('coemoa_c', 'spea2'     ),
              ('ackley',   'nsga2'     ),
              ('coemoa_e', 'hgs_ibea'  ),
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
