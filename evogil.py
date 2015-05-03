#!/usr/bin/env python3
"""EvoGIL helper.

Usage:
  evogil.py -h | --help 
  evogil.py violin [options]
  evogil.py statistics [options]
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

Algorithms:
  MO-HGS+NSGA-II

Problems:
  ZDT6
"""
from docopt import docopt

from multiprocessing import Pool
import time
import evotools.stats
import random
import pathlib
import json
from math import sqrt
import numpy
from functools import reduce
import os
import os
import matplotlib.pyplot as plt
from numpy.linalg import LinAlgError
from pathlib import Path
from contextlib import contextmanager
from ep.utils import ea_utils
import problems.ackley.problem as ackley
import problems.coemoa_a.problem as zdt1
import problems.coemoa_b.problem as zdt2
import problems.coemoa_c.problem as zdt3
import problems.coemoa_d.problem as zdt4
import problems.coemoa_e.problem as zdt6


PLOTS_DIR = 'plots'

SPEA_LS = '-'
NSGA_LS = '--'
IBEA_LS = ':'
SPEA_M = 'o'
NSGA_M = '*'
IBEA_M = '^'
BARE_CL = '0.8'
IMGA_CL = '0.4'
HGS_CL = '0.0'

algos = {'spea2': ('SPEA2', SPEA_LS, SPEA_M, BARE_CL), 'nsga2': ('NSGAII', NSGA_LS, NSGA_M, BARE_CL),
         'ibea': ( 'IBEA', IBEA_LS, IBEA_M, BARE_CL),
         'imga_spea2': ('IMGA-SPEA2', SPEA_LS, SPEA_M,  IMGA_CL),
         'imga_nsga2': ( 'IMGA-NSGAII', NSGA_LS,NSGA_M, IMGA_CL), 'imga_ibea': ('IMGA-IBEA', IBEA_LS, IBEA_M, IMGA_CL),
         'hgs_spea2': ( 'HGS-SPEA2', SPEA_LS, SPEA_M, HGS_CL),
         'hgs_nsga2': ( 'HGS-NSGAII', NSGA_LS, NSGA_M, HGS_CL), 'hgs_ibea': ( 'HGS-IBEA', IBEA_LS, IBEA_M, HGS_CL)}
algos_order = ['spea2', 'nsga2', 'ibea', 'imga_spea2', 'imga_nsga2', 'imga_ibea', 'hgs_spea2', 'hgs_nsga2', 'hgs_ibea']



################################################################################
################################################################################
################################################################################

def run_parallel(argv):
    p = Pool(5)
    print(p.map(run_parallel__f, [1, 2, 3, 4, 5, 6, 7, 8, 9]))

def run_parallel__f(x):
    time.sleep(1)
    return x*x

################################################################################
################################################################################
################################################################################

metric_names = [ ("distance_from_pareto", "dst from pareto"),
                 ("distribution", "distribution"),
                 ("extent", "extent")
               ]

def iterate_serialized():
    root = pathlib.Path('jsoned')
    for d_problem in [p_problem
                      for p_problem in root.iterdir()
                      if p_problem.is_dir()]:
        sd_problem = False
        for d_algorithm in [p_algo
                            for p_algo in d_problem.iterdir()
                            if p_algo.is_dir()]:
            sd_algorithm = False
            for d_testname in [p_testname
                               for p_testname in d_algorithm.iterdir()
                               if p_testname.is_dir()]:
                sd_testname = False
                for d_budget in sorted([p_budget
                                        for p_budget in d_testname.iterdir()
                                        if p_budget.is_dir()],
                                       key=lambda x: int(x.name)):
                    sd_budget = False


                    results = {}
                    for metrics_name_long, metrics_name in metric_names:
                        for result_file in d_budget.glob(metrics_name_long + "*.json"):
                            data = []
                            cost = []
                            with result_file.open(mode="r") as fh:
                                test_results = json.load(fh)
                                data.append(test_results["metrics"])
                                cost.append(test_results["cost"])
                                results[metrics_name_long] = (data, cost)

                        yield { 'd_problem':    d_problem,
                                'sd_problem':   sd_problem,

                                'd_algorithm':  d_algorithm,
                                'sd_algorithm': sd_algorithm,

                                'd_testname':   d_testname,
                                'sd_testname':  sd_testname,

                                'd_budget':     d_budget,
                                'sd_budget':    sd_budget,

                                'data':         data,
                                'cost':         cost,

                                'metrics_name_long': metrics_name_long,
                                'metrics_name':      metrics_name
                              }

                        sd_problem = True
                        sd_algorithm = True
                        sd_testname = True
                        sd_budget = True


def statistics(args):
    badbench = []
    cost_badbench = []
    
    for loop in iterate_serialized():

        d_problem    = loop['d_problem']
        sd_problem   = loop['sd_problem']
        
        d_algorithm  = loop['d_algorithm']
        sd_algorithm = loop['sd_algorithm']
        
        d_testname   = loop['d_testname']
        sd_testname  = loop['sd_testname']
        
        d_budget     = loop['d_budget']
        sd_budget    = loop['sd_budget']

        data         = loop['data']
        cost         = loop['cost']
        len_data = len(data)

        metrics_name_long = loop['metrics_name_long']
        metrics_name      = loop['metrics_name']

        def abstract(data_process):
            q1 = numpy.percentile(data_process, 25)
            q3 = numpy.percentile(data_process, 75)
            iq = q3 - q1
            low_inn_fence = q1 - 1.5*iq
            upp_inn_fence = q3 + 1.5*iq
            low_out_fence = q1 - 3*iq
            upp_out_fence = q3 + 3*iq
            # noinspection PyRedeclaration
            extr_outliers = len([x for x in data_process if (x < low_out_fence or upp_out_fence < x)])
            # noinspection PyRedeclaration
            mild_outliers = len([x for x in data_process if (x < low_inn_fence or upp_inn_fence < x)]) - extr_outliers
            extr_outliers = extr_outliers > 0 and "{0:6.2f}%".format(extr_outliers * 100.0 / len(data_process)) or "--"
            mild_outliers = mild_outliers > 0 and "{0:6.2f}%".format(mild_outliers * 100.0 / len(data_process)) or "--"
            metrics_nooutliers = evotools.stats.average([x for x in data_process if low_inn_fence <= x <= upp_inn_fence])
            try:
                mean_nooutliers = float(evotools.stats.average([x for x in data_process if low_inn_fence <= x <= upp_inn_fence]))
                variance_nooutliers = [(x - mean_nooutliers) ** 2 for x in data_process if low_inn_fence <= x <= upp_inn_fence]
                stdev_nooutliers = sqrt(evotools.stats.average(variance_nooutliers))
            except ValueError:
                stdev_nooutliers = -float("inf")

            btstrpd = evotools.stats.bootstrap(data_process, evotools.stats.average, int(args['--bootstrap']), int(len(data_process) * 0.66), 0.025)

            goodbench = "✓"
            try:
                mean = float(evotools.stats.average(data_process))
                variance = [(x - mean) ** 2 for x in data_process]
                stdev = sqrt(evotools.stats.average(variance))
                lower = mean - 3 * stdev
                upper = mean + 3 * stdev
                if len([x for x in data_process if lower <= x <= upper]) < 0.95 * len(data_process):
                    goodbench = "╳╳╳╳╳"
            except ValueError:
                stdev = float("inf")
                goodbench = "?"

            try:
                mean_nooutliers_diff = 100.0 * (mean_nooutliers - mean) / mean
            except ZeroDivisionError:
                mean_nooutliers_diff = float("inf")

            try:
                stdev_nooutliers_diff = 100.0 * (stdev_nooutliers - stdev) / stdev
            except ZeroDivisionError:
                stdev_nooutliers_diff = float("inf")

            dispersion_warn = ""
            try:
                pr_dispersion = 100.0 * (float(btstrpd["to"]) - float(btstrpd["from"])) / btstrpd["metrics"]
                if abs(pr_dispersion) > 30.:
                    dispersion_warn = " HIGH"
            except ZeroDivisionError:
                pr_dispersion = float("+Infinity")

            return low_inn_fence, upp_inn_fence, low_out_fence, upp_out_fence, stdev, mean, lower, upper, goodbench, btstrpd, stdev, mild_outliers, extr_outliers, metrics_nooutliers, mean_nooutliers_diff, stdev_nooutliers, stdev_nooutliers_diff, pr_dispersion, dispersion_warn

        low_inn_fence, upp_inn_fence, low_out_fence, upp_out_fence, stdev, mean, lower, upper, goodbench, btstrpd, stdev, mild_outliers, extr_outliers, metrics_nooutliers, mean_nooutliers_diff, stdev_nooutliers, stdev_nooutliers_diff, pr_dispersion, dispersion_warn = abstract(data)
        cost_low_inn_fence, cost_upp_inn_fence, cost_low_out_fence, cost_upp_out_fence, cost_stdev, cost_mean, cost_lower, cost_upper, cost_goodbench, cost_btstrpd, cost_stdev, cost_mild_outliers, cost_extr_outliers, cost_metrics_nooutliers, cost_mean_nooutliers_diff, cost_stdev_nooutliers, cost_stdev_nooutliers_diff, cost_pr_dispersion, cost_dispersion_warn = abstract(cost)

        probname = str(d_problem.name)
        if not sd_problem:
            print("=" * 436)


        algoname = not sd_algorithm and str(d_algorithm.name) or ""

        test_name = not sd_testname and str(d_testname.name)[5:] or ""
        fields = [
            ("PROBLEM"                    , [9],          "{probname:{0}}"                                                                                   ),
            ("ALGO"                       , [10],         "{algoname:{0}}"                                                                                   ),
            ("TEST"                       , [24],         "{test_name:{0}}"                                                                                  ),
            ("N"                          , [2],          "{len_data:>{0}}"                                                                                   ),
            ("Budgt"                      , [5],          "{budg_cost!s:>{0}}"                                                                               ),
            ("METRICS OY"                 , [15],         "{metrics_name:^{0}}"                                                                              ),
            ("✓"                          , [5],          "{goodbench:^{0}}"                                                                                 ),
            ("RESULT, confidence interval", [10,10,10,6], "{btstrpd[from]: >0{0}.3f} ≤ {btstrpd[metrics]: >{1}.3f} ≤ {btstrpd[to]: >0{2}.3f}"                ),
            ("σ"                          , [10],         "{stdev: >{0}.3f}"                                                                                 ),
            ("OUTLIERS"                   , [7,7,12],     "{mild_outliers:>{0}} mild {extr_outliers:>{1}} extr."                                             ),
            ("RES w/o outliers"           , [10,10,4],    "{metrics_nooutliers:>{0}.3f} ({mean_nooutliers_diff:>+{1}.3f}%)"                                  ),
            ("σ w/o outliers"             , [10,10,4],    "{stdev_nooutliers:>{0}.3f} ({stdev_nooutliers_diff:>{1}.3f}%)"                                    ),
            ("(C INT)/METRICS"            , [7,10,2],     "{pr_dispersion: >{0}.3f}% {dispersion_warn:<{1}}"                                                 ),
            ("OX"                         , [5],          "cost "                                                                                            ),
            ("✓"                          , [5],          "{cost_goodbench:^{0}}"                                                                            ),
            ("RESULT, confidence interval", [10,10,10,6], "{cost_btstrpd[from]: >0{0}.3f} ≤ {cost_btstrpd[metrics]: >{1}.3f} ≤ {cost_btstrpd[to]: >0{2}.3f}" ),
            ("σ"                          , [10],         "{cost_stdev: <{0}.3f}"                                                                            ),
            ("OUTLIERS"                   , [7,7,12],     "{cost_mild_outliers:>{0}} mild {cost_extr_outliers:>{1}} extr."                                   ),
            ("RES w/o outliers"           , [10,10,4],    "{cost_metrics_nooutliers:>{0}.3f} ({cost_mean_nooutliers_diff:>+{1}.3f}%)"                        ),
            ("σ w/o outliers"             , [10,10,4],    "{cost_stdev_nooutliers:>{0}.3f} ({cost_stdev_nooutliers_diff:>{1}.3f}%)"                          ),
            ("(C INT)/METRICS"            , [7,10,2],     "{cost_pr_dispersion: >{0}.3f}% {cost_dispersion_warn:<{1}}"                                       )
        ]
        if not sd_testname:
            print('..'.join('[{0:^{1}}]'.format(head,sum(width)) for (i, (head,width,var)) in enumerate(fields)) + "..", flush=True)

        budg_cost = not sd_budget and str(d_budget.name) or ""

        lcls = locals()
        print(" " + " :: ".join(var.format(*width, **lcls) for (i, (head,width,var)) in enumerate(fields)) + " :: ", flush=True)

        def abstract_analysis(mean_nooutliers_diff_process, goodbench_process, lower_process, upper_process, data_process, low_inn_fence_process, upp_inn_fence_process, low_out_fence_process, upp_out_fence_process, stdev_process, mean_process, badbench_process, prefix):
            prefix = " " * prefix
            if goodbench_process != "✓":
                outliers = len([x for x in data_process if lower_process <= x <= upper_process])
                print(
                    "{prefix}:: Suspicious result analysis:\n"
                    "{prefix}::             {0:>2} / {1:2} ({4:7.3f}%) out of [ {2:>18.13} ; {3:<18.13} ]\n"
                    "{prefix}::                                                            Δ {7:<18.13}\n"
                    "{prefix}::                               Bounds: [ {5:>18.13} ; {6:<18.13} ]\n"
                    "{prefix}::                                                            Δ {8:<18.13}".format(
                        outliers, len(data_process), lower_process, upper_process, 100.0 * outliers / len(data_process), min(data_process), max(data_process), upper_process - lower_process, max(data_process)-min(data_process),prefix=prefix)
                )
                print(
                    "{prefix}:: Values".format(prefix=prefix))
                def aux(x):
                    try:
                        return abs(x - mean_process) * 100.0 / stdev_process
                    except ZeroDivisionError:
                        return float("inf")
                print(''.join(
                    "{prefix}:: {0:>30.20}  = avg {1:<+30} = avg {3:+8.3f}% ⨉ σ | {2:17} {4:17} {5:17}\n".format(
                        x,
                        x - mean_process,
                        (lower_process <= x <= upper_process) and "(out of mean±3σ)" or "",
                        aux(x),
                        ((low_out_fence_process <= x < low_inn_fence_process) or (upp_inn_fence_process <= x < upp_out_fence_process)) and " (mild outlier)" or "",
                        ((x < low_out_fence_process) or (upp_out_fence_process < x)) and "(EXTREME outlier)" or "",
                        prefix=prefix
                    )
                    for x in data_process),
                    end=''
                )
                if abs(mean_nooutliers_diff_process) > 10.:
                    badbench_process.append(d_budget)
                    print("{prefix}:: #################### ################################################################### ####################".format(prefix=prefix))
                    print("{prefix}:: #################### Mean of results changed a lot (> 10%), so probably UNTRUSTED result ####################".format(prefix=prefix))
                    print("{prefix}:: #################### ################################################################### ####################".format(prefix=prefix))
                else:
                    print("{prefix}:: Mean of results changed a little (< 10%), so probably that's all okay".format(prefix=prefix))
        abstract_analysis(mean_nooutliers_diff, goodbench, lower, upper, data, low_inn_fence, upp_inn_fence, low_out_fence, upp_out_fence, stdev, mean, badbench, prefix=62)
        abstract_analysis(cost_mean_nooutliers_diff, cost_goodbench, cost_lower, cost_upper, [float(x) for x in cost], cost_low_inn_fence, cost_upp_inn_fence, cost_low_out_fence, cost_upp_out_fence, cost_stdev, cost_mean, cost_badbench, prefix=253)



    if badbench or cost_badbench:
        print("#" * 436)
        for i in badbench:
            print(">>> " + str(i))


################################################################################
################################################################################
################################################################################

@contextmanager
def plt_figure():
    yield
    plt.close('all')


def prepare_data(data):
    l = list(filter(lambda d: all([v != 0 for v in d]), data))
    if l != data:
        print(data)
        print(l)
        print()
    return l


def violin(*args, **kwargs):
    global_data = {}

    for loop in iterate_serialized():
        d_problem    = loop['d_problem']
        sd_problem   = loop['sd_problem']
        
        d_algorithm  = loop['d_algorithm']
        sd_algorithm = loop['sd_algorithm']
        
        d_testname   = loop['d_testname']
        sd_testname  = loop['sd_testname']
        
        d_budget     = loop['d_budget']
        sd_budget    = loop['sd_budget']

        data         = loop['data']
        cost         = loop['cost']
        len_data = len(data)

        metrics_name_long = loop['metrics_name_long']
        metrics_name      = loop['metrics_name']


        key = (d_problem.name, metrics_name_long)
        if key not in global_data:
            global_data[(d_problem.name, metrics_name_long)] = {}

        global_data[(d_problem.name, metrics_name_long)][d_algorithm.name] = data

    for problem, metric in global_data:
        try:
            algo_data = global_data[(problem, metric)]

            data = prepare_data([algo_data[algo_key] for algo_key in algos_order])

            with plt_figure():
                if metric == 'distance_from_pareto':
                    metric = 'distance from Pareto front'
                    if problem == 'ackley':
                        plt.ylim([0.0001, 10])
                    plt.yscale('log')
                if metric == 'distribution':
                    if problem == 'ackley' or problem == 'coemoa_b':
                        plt.ylim([-0.1, 1.0])
                if metric == 'extent':
                    if problem == 'ackley':
                        plt.ylim([-0.5, 4.0])

                plt.figure(num=None, facecolor='w', edgecolor='k')
                # plt.yscale('log')
                x_index = range(1, len(algos) + 1)
                plt.ylabel(metric, fontsize=20)
                plt.xticks(x_index, [algos[a][0] for a in algos_order], rotation=20)
                for i in x_index:
                    plt.axvline(i, lw=0.9, c='#AFAFAF', alpha=0.5)
                plt.tick_params(axis='both',  labelsize=15)

                result = plt.violinplot(data, showmeans=True,
                               showextrema=True, showmedians=True, widths=0.8)

                for pc in result['bodies']:
                    pc.set_facecolor('0.8')
                    # pc.set_sizes([0.8])


                result['cbars'].set_color('black')
                result['cmeans'].set_color('black')
                result['cmins'].set_color('black')
                result['cmaxes'].set_color('black')
                result['cmedians'].set_color('black')

                result['cmeans'].set_linewidths([2])


                plt.tight_layout()
                os.makedirs(PLOTS_DIR, exist_ok=True)
                os.makedirs(os.path.join(PLOTS_DIR, 'plots_violin'), exist_ok=True)
                problem_moea = problem.replace('emoa', 'moea')
                metric_short = metric.replace('distance from Pareto front', 'dst')
                fig_path = os.path.join(PLOTS_DIR, 'plots_violin', problem_moea + '_' + metric_short + '.pdf')
                plt.savefig(fig_path)

        except KeyError as e:
            print('Missing algo: {}, (problem: {}, metrics: {}'.format(e, problem, metric))
        except LinAlgError as e:
            print('Zero vector? : {}, {}'.format(problem, metric))


################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    argv = docopt(__doc__, version='Naval Fate 2.0')
    print(argv)

    if argv['run_parallel']:
        run_parallel(argv)
    elif argv['statistics']:
        statistics(argv)
    elif argv['violin']:
        violin(argv)
