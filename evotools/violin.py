# base
import os
from contextlib import contextmanager

# numpy + matplotlib
import collections
import matplotlib.pyplot as plt
from numpy.linalg import LinAlgError

# self
from evotools import config
from evotools.pictures import algos, algos_order, PLOTS_DIR
from evotools.ranking import best_func
from evotools.serialization import RunResult
from evotools.stats_bootstrap import yield_analysis


@contextmanager
def plt_figure():
    try:
        yield
    finally:
        plt.close('all')


def prepare_data(data):
    l = list(filter(lambda d: all([v != 0 for v in d]), data))
    if l != data:
        print(data)
        print(l)
        print()
    return l


def violin(args, queue):
    global_data = collections.defaultdict(dict)

    boot_size = int(args['--bootstrap'])

    for problem_name, problem_mod, algorithms in RunResult.each_result(config.RESULTS_DIR):
        for algo_name, budgets in algorithms:
            for metric_name, metric_name_long, data_process in list(budgets)[-1]["analysis"]:
                if metric_name in best_func:
                    data_process = list(x() for x in data_process)
                    global_data[(problem_name, metric_name)][algo_name] = data_process

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
                    if problem == 'ackley' or problem == 'ZDT2':
                        plt.ylim([-0.1, 1.0])
                if metric == 'extent':
                    if problem == 'ackley':
                        plt.ylim([-0.5, 4.0])

                plt.figure(num=None, facecolor='w', edgecolor='k')
                # plt.yscale('log')
                x_index = range(1, len(algos_order) + 1)
                plt.ylabel(metric, fontsize=20)
                plt.xticks(x_index, [algos[a][0] for a in algos_order], rotation=30)
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
                # os.makedirs(PLOTS_DIR, exist_ok=True)
                # os.makedirs(os.path.join(PLOTS_DIR, 'plots_violin'), exist_ok=True)
                problem_moea = problem.replace('emoa', 'moea')
                metric_short = metric.replace('distance from Pareto front', 'dst')
                fig_path = PLOTS_DIR / 'plots_violin' / '{}_{}.eps'.format( problem_moea, metric_short)
                print(fig_path)
                plt.savefig(str(fig_path))

        except KeyError as e:
            print('Missing algo: {}, (problem: {}, metrics: {}'.format(e, problem, metric))
        except LinAlgError as e:
            print('Zero vector? : {}, {}: {}'.format(problem, metric, e))
