# base
import copy
import logging
import multiprocessing
import time
import collections
import operator

from importlib import import_module
from contextlib import suppress

from evotools.ea_utils import gen_population
from evotools import run_config

from functools import partial
import traceback
from evotools.log_helper import get_logger
from evotools.timing import log_time, process_time
from evotools.timing import system_time

logger = get_logger(__name__)


def run_parallel(args):
    order = [
              ('ZDT6',     'HGS+NSGAII' , None),
              ('ZDT4',     'HGS+NSGAII' , None),
              ('ZDT4',     'IMGA+NSGAII', None),
              ('ZDT3',     'HGS+NSGAII' , None),
              ('ZDT1',     'HGS+NSGAII' , None),
              ('ZDT2',     'HGS+NSGAII' , None),
              ('ZDT4',     'NSGAII'     , None),
              ('ZDT6',     'NSGAII'     , None),
              ('kursawe',  'HGS+NSGAII' , None),
              ('ZDT3',     'NSGAII'     , None),
              ('ZDT1',     'NSGAII'     , None),
              ('ZDT2',     'NSGAII'     , None),
              ('ZDT6',     'IMGA+NSGAII', None),
              ('ZDT3',     'IMGA+NSGAII', None),
              ('ZDT2',     'IMGA+NSGAII', None),
              ('ZDT1',     'IMGA+NSGAII', None),
              ('ZDT2',     'HGS+SPEA2'  , None),
              ('ZDT1',     'HGS+SPEA2'  , None),
              ('kursawe',  'IMGA+NSGAII', None),
              ('kursawe',  'NSGAII'     , None),
              ('ZDT4',     'HGS+SPEA2'  , None),
              ('ZDT4',     'IBEA'       , None),
              ('ZDT4',     'IMGA+IBEA'  , None),
              ('kursawe',  'IBEA'       , None),
              ('kursawe',  'IMGA+IBEA'  , None),
              ('kursawe',  'SPEA2'      , None),
              ('kursawe',  'IMGA+SPEA2' , None),
              ('ZDT6',     'IBEA'       , None),
              ('ZDT6',     'IMGA+IBEA'  , None),
              ('kursawe',  'HGS+SPEA2'  , None),
              ('ZDT3',     'HGS+SPEA2'  , None),
              ('ZDT3',     'IBEA'       , None),
              ('ZDT3',     'IMGA+IBEA'  , None),
              ('ZDT4',     'IMGA+SPEA2' , None),
              ('ZDT2',     'IMGA+IBEA'  , None),
              ('ZDT2',     'IBEA'       , None),
              ('ZDT1',     'IBEA'       , None),
              ('kursawe',  'HGS+IBEA'   , None),
              ('ZDT1',     'IMGA+IBEA'  , None),
              ('ZDT4',     'HGS+IBEA'   , None),
              ('ZDT6',     'HGS+SPEA2'  , None),
              ('ZDT3',     'HGS+IBEA'   , None),
              ('ZDT1',     'HGS+IBEA'   , None),
              ('ZDT2',     'HGS+IBEA'   , None),
              ('ZDT1',     'IMGA+SPEA2' , None),
              ('ZDT2',     'IMGA+SPEA2' , None),
              ('ZDT3',     'IMGA+SPEA2' , None),
              ('ZDT6',     'IMGA+SPEA2' , None),
              ('ackley',   'IMGA+NSGAII', None),
              ('ackley',   'HGS+NSGAII' , None),
              ('ZDT4',     'SPEA2'      , None),
              ('ZDT1',     'SPEA2'      , None),
              ('ZDT6',     'SPEA2'      , None),
              ('ZDT2',     'SPEA2'      , None),
              ('ZDT3',     'SPEA2'      , None),
              ('ackley',   'NSGAII'     , None),
              ('ZDT6',     'HGS+IBEA'   , None),
              ('ackley',   'IMGA+SPEA2' , None),
              ('ackley',   'HGS+SPEA2'  , None),
              ('ackley',   'SPEA2'      , None),
              ('ackley',   'IMGA+IBEA'  , None),
              ('ackley',   'IBEA'       , None),
              ('ackley',   'HGS+IBEA'   , None),
              ('parabol',  'HGS+SPEA2'  , None),
              ('parabol',  'HGS+IBEA'   , None),
              ('parabol',  'HGS+NSGAII' , None)
            ]

    if args['--algo']:
        algos = args['--algo'].lower().split(',')
        order = [ (problem, algo, budget)
                  for problem, algo, budget
                  in order
                  if algo.lower() in algos
                ]

    if args['--problem']:
        problems = args['--problem'].lower().split(',')
        order = [ (problem, algo, budget)
                  for problem, algo, budget
                  in order
                  if problem.lower() in problems
                ]

    print("Selected following tests:")
    for problem, algo, budget in order:
        print("  {problem:12} :: {algo:12}".format(**locals()))

    order = [ test
              for test in order
              for i in range(int(args['-N']))
            ]


    p = multiprocessing.Pool(int(args['-j']))

    wall_time = -time.perf_counter()
    results = p.map(worker, order)
    wall_time += time.perf_counter()

    proc_times = sum( res
                      for res
                      in results
                      if res is not None
                    )
    errors = [ str((alg, prob, budg))
               for res, (prob, alg, budg)
               in zip(results, order)
               if res is None
             ]

    speedup = proc_times / wall_time

    print("########################################")
    print("SUMMARY:")
    print("  wall time:     {wall_time:7.3f} s\n"\
          "  CPU+user time: {proc_times:7.3f}s\n"\
          "  est. speedup:  {speedup:7.3f}x"
          .format(**locals()))
    if errors:
        errors = '\n                 '.join(errors)
        print("  errors:        {errors:>3}"
              .format(**locals()))

    summary = collections.defaultdict(float)
    for bench, res in zip(order, results):
        summary[bench] += res or 0.0


    print("RUNNING TIME LIST:")
    for (prob, alg, budgets), timesum in sorted( summary.items(),
                                                 key=operator.itemgetter(1),
                                                 reverse=True
                                               ):
        prob_show = "'" + prob + "'"
        alg_show = "'" + alg + "'"
        avg_time = timesum / float(args['-N'])
        budgets = str(budgets)
        print("  ({prob_show:16}, {alg_show:16}, {budgets:30}),  # {avg_time:7.3f}s".format(**locals()))


def worker(args):
    logger.debug("Starting the worker. args:%s", args)
    problem, algo, budgets = args
    if not budgets:
        budgets = run_config.metaconfig_budgets

    drivers = algo.split('+')

    try:
        final_driver = None
        for driver_pos, driver in list(enumerate(drivers))[::-1]:
            final_driver = prepare(driver,
                                   problem,
                                   final_driver,
                                   drivers, driver_pos
                                  )

        gen = final_driver().population_generator()

        total_cost, result = 0, None

        proc_time = []
        with log_time(system_time, logger, "Processing done in {time_res}s", out=proc_time):
            proxy = None
            logger.debug("Starting processing")
            while total_cost <= 100:
                logger.debug("Waiting for proxy")
                with log_time(system_time, logger, "Got proxy in {time_res}s"):
                    proxy = next(gen)
                logger.debug("Proxy.cost:%d", proxy.cost)
                total_cost += proxy.cost
                logger.debug("total_cost:%d", total_cost)
            logger.debug("End loop, total_cost:%d", total_cost)
            logger.debug("Final population: %s", proxy.finalized_population())

        return proc_time[-1]

    except Exception as e:
        print(traceback.format_exc())


def prepare(algo, problem, driver=None, all_drivers=None, driver_pos=0):
    logger.debug("Starting preparation")

    if not all_drivers:
        all_drivers = []

    logger.debug("Preparing %s for %s", algo, problem)
    logger.debug("driver:%s", driver)

    algo_mod   = '.'.join(['algorithms', algo, algo])
    algo_mod   = import_module(algo_mod)
    algo_class = getattr(algo_mod, algo)

    problem_mod = '.'.join(['problems', problem, 'problem'])
    problem_mod = import_module(problem_mod)

    # START WITH META-CONFIG
    logger.debug("Starting with config containing meta-parameters")
    config = {
        "__metaconfig__populationsize": run_config.metaconfig_populationsize
    }
    logger.debug("config: %s", config)

    ################################################################################
    # CUSTOMS FOR PROBLEM
    update = {"dims": problem_mod.dims, "fitnesses": problem_mod.fitnesses}
    logger.debug("Per-problem config: %s", update)
    config.update(update)
    logger.debug("config: %s", config)

    ################################################################################
    descr = "DRIVER ASSIGNMENT"
    if driver:
        update = {"driver": driver}
        config.update(update)
        logger.debug("Assigning driver: %s", update)
        config.update(update)
        logger.debug("config: %s", config)

    ################################################################################
    descr = "CUSTOMS FOR ALGORITHM"
    # example key: SPEA2
    # example key: HGS
    # example key: IMGA
    with suppress(KeyError):
        key = algo
        update = run_config.algo_base[key]
        logger.debug("%s %s: %s",
                     descr,
                     "| by algo dict key:", key, "\n    <<", ', '.join(run_config.algo_base[key]),
                     update)
        config.update(update)
        logger.debug("config: %s", config)

    ################################################################################
    descr = "CUSTOMS FOR ALGORITHM + SUBDRIVERS"
    # example key: (SPEA2, ()          )
    # example key: (HGS,   (SPEA2)     )
    # example key: (IMGA,  (HGS, SPEA2))
    with suppress(KeyError):
        key = (algo,
               tuple(all_drivers[driver_pos+1:])
               )
        update = run_config.algo_base[key]
        logger.debug("%s %s: %s",
                     descr,
                     "| by algo dict key:", key, "\n    <<", ', '.join(run_config.algo_base[ key ]),
                     update)
        config.update(update)
        logger.debug("config: %s", config)

    ################################################################################
    descr = "CUSTOMS FOR PARENTS + ALGORITHM"
    # example key: ((IMGA, HGS), SPEA2)
    # example key: ((IMGA,),     HGS  )
    # example key: ((),          IMGA )
    with suppress(KeyError):
        key = (tuple(all_drivers[:driver_pos]),
               algo
              )
        update = run_config.algo_base[key]
        logger.debug("%s %s: %s",
                     descr,
                     "| by algo dict key:", key, "\n    <<", ', '.join(run_config.algo_base[ key ]),
                     update)
        config.update(update)
        logger.debug("config: %s", config)

    ################################################################################
    descr = "CUSTOMS FOR PARENTS + ALGORITHM + SUBDRIVERS"
    # example key: ((IMGA, HGS), SPEA2, ()          )
    # example key: ((IMGA,),     HGS,   (SPEA2)     )
    # example key: ((),          IMGA,  (HGS, SPEA2))
    with suppress(KeyError):
        key = (tuple(all_drivers[:driver_pos]),
               algo,
               tuple(all_drivers[driver_pos+1:])
              )
        update = run_config.algo_base[key]
        logger.debug("%s %s: %s",
                     descr,
                     "| by algo dict key:", key, "\n    <<", ', '.join(run_config.algo_base[ key ]),
                     update)
        config.update(update)
        logger.debug("config: %s", config)

    ################################################################################
    descr = "CUSTOMS (simpl)"
    # example key: (SPEA2, ackley)
    # example key: (SPEA2, zdt1)
    # example key: (HGS, ackley)
    # example key: (HGS, zdt1)
    # example key: (IMGA, ackley)
    # example key: (IMGA, zdt1)
    with suppress(KeyError):
        key = ( algo,
                problem
              )
        update = run_config.cust_base[key]
        logger.debug("%s %s: %s",
                     descr,
                     "| by cust dict key:", key, "\n    <<", ', '.join(run_config.cust_base[ key ]),
                     update)
        config.update(update)
        logger.debug("config: %s", config)

    ################################################################################
    descr = "CUSTOMS"
    # example key: ((IMGA, HGS), SPEA2, (),           ackley)
    # example key: ((IMGA, HGS), SPEA2, (),           zdt1)
    # example key: ((IMGA),      HGS,   (SPEA2),      ackley)
    # example key: ((IMGA),      HGS,   (SPEA2),      zdt1)
    # example key: ((),          IMGA,  (HGS, SPEA2), ackley)
    # example key: ((),          IMGA,  (HGS, SPEA2), zdt1)
    with suppress(KeyError):
        key = (tuple(all_drivers[:driver_pos]),
               algo,
               tuple(all_drivers[driver_pos+1:]),
               problem
              )
        update = run_config.cust_base[key]
        logger.debug("%s %s: %s",
                     descr,
                     "| by cust dict key:", key, "\n    <<", ', '.join(run_config.cust_base[ key ]),
                     update)
        config.update(update)
        logger.debug("config: %s", config)

    ################################################################################
    descr = "CUSTOMS FOR ALGORITHM"
    # example fun: init_alg_SPEA2
    # example fun: init_alg_HGS
    # example fun: init_alg_IMGA
    with suppress(AttributeError):
        key = "init_alg_" + algo
        updater = getattr(run_config, key)
        logger.debug("%s %s: %s: %s",
                     descr,
                     "| by algo fun:",
                     key,
                     updater
                     )
        updater(config, problem_mod)
        logger.debug("config: %s", config)

    ################################################################################
    descr = "CUSTOMS FOR ALGORITHM + SUBDRIVERS"
    # example fun: init_alg_HGS__SPEA2
    # example fun: init_alg_IMGA__HGS_SPEA2
    with suppress(AttributeError):
        key = "init_alg_" + algo + '__' + '_'.join(all_drivers[driver_pos+1:])
        updater = getattr(run_config, key)
        logger.debug("%s %s: %s: %s",
                     descr,
                     "| by algo fun:",
                     key,
                     updater
                     )
        updater(config, problem_mod)
        logger.debug("config: %s", config)

    ################################################################################
    descr = "CUSTOMS FOR PARENTS + ALGORITHM"
    # example fun: init_alg_IMGA_HGS__SPEA2
    # example fun: init_alg_IMGA__HGS
    with suppress(AttributeError):
        key = "init_alg_" + '_'.join(all_drivers[:driver_pos]) + '__' + algo
        updater = getattr(run_config, key)
        logger.debug("%s %s: %s: %s",
                     descr,
                     "| by algo fun:",
                     key,
                     updater
                     )
        updater(config, problem_mod)
        logger.debug("config: %s", config)

    ################################################################################
    descr = "CUSTOMS FOR PARENTS + ALGORITHM + SUBDRIVERS"
    # example fun: init_alg_IMGA__HGS__SPEA2
    with suppress(AttributeError):
        key = "init_alg_" + '_'.join(all_drivers[:driver_pos]) + '__' + algo + '__' + '_'.join(all_drivers[driver_pos+1:])
        updater = getattr(run_config, key)
        logger.debug("%s %s: %s: %s",
                     descr,
                     "| by algo fun:",
                     key,
                     updater
                     )
        updater(config, problem_mod)
        logger.debug("config: %s", config)

    ################################################################################
    descr = "CUSTOMS FOR PROBLEM"
    # example key: ackley
    # example key: zdt1
    with suppress(KeyError):
        key = problem
        update = run_config.prob_base[key]
        logger.debug("%s %s: %s",
                     descr,
                     "| by prob dict key:", key, "\n    <<", ', '.join(run_config.prob_base[ key ]),
                     update)
        config.update(update)
        logger.debug("config: %s", config)

    ################################################################################
    descr = "CUSTOMS FOR PROBLEM"
    # example fun: init_prob_ackley
    with suppress(AttributeError):
        key = "init_prob_" + '_'.join(all_drivers[:driver_pos]) + '__' + algo + '__' + '_'.join(all_drivers[driver_pos+1:])
        updater = getattr(run_config, key)
        logger.debug("%s %s: %s: %s",
                     descr,
                     "| by prob fun:",
                     key,
                     updater
                     )
        updater(config, problem_mod)
        logger.debug("config: %s", config)

    ################################################################################
    descr = "CUSTOMS"
    # example fun: init_cust_SPEA2___ackley
    # example fun: init_cust_SPEA2___zdt1
    # example fun: init_cust_IMGA_HGS__SPEA2___ackley
    # example fun: init_cust_IMGA_HGS__SPEA2___zdt1
    # example fun: init_cust_IMGA__HGS__SPEA2___ackley
    # example fun: init_cust_IMGA__HGS__SPEA2___zdt1
    # example fun: init_cust__IMGA__HGS_SPEA2___ackley
    # example fun: init_cust__IMGA__HGS_SPEA2___zdt1
    with suppress(AttributeError):
        key = "init_cust_" + '_'.join(all_drivers[:driver_pos]) + '__' + algo + '__' + '_'.join(all_drivers[driver_pos+1:])
        updater = getattr(run_config, key)
        logger.debug("%s %s: %s: %s",
                     descr,
                     "| by cust fun:",
                     key,
                     updater
                     )
        updater(config, problem_mod)
        logger.debug("config: %s", config)

    ################################################################################
    descr = "GENERATING POPULATION"
    if "population" not in config:
        initial_population = gen_population(config["__metaconfig__populationsize"], problem_mod.dims)
        update = {"population": initial_population}
        logger.debug("%s (size: %s, dims: %s): %s",
                     descr,
                     config["__metaconfig__populationsize"],
                     problem_mod.dims,
                     initial_population)
        config.update(update)

    ################################################################################
    # DROPPING TRASH
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("dropping trash from config: %s",
                     {k: v
                      for k, v
                      in config.items()
                      if k.startswith('__metaconfig__')
                      })
    config = {k: v
              for k, v
              in config.items()
              if not k.startswith('__metaconfig__')
             }

    try:
        algo_class(**config)
    except Exception as e:
        logger.exception("Class creation error.", exc_info=e)
        raise e
    else:
        logger.info("Preparing (algo=%s, problem=%s, driver=%s, all_drivers=%s, driver_pos=%d) done, class obj created",
                    algo,
                    problem,
                    driver,
                    all_drivers,
                    driver_pos)

    instance = partial(algo_class, **config)
    logger.info("Dropping this dummy obj, returning partial instead: %s",
                instance)
    return instance

