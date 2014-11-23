from functools import reduce
import pickle
import os

import matplotlib.pyplot as plt
from numpy.linalg import LinAlgError
from pathlib import Path
from contextlib import contextmanager
from pictures_from_stats_new import algos, algos_order, PLOTS_DIR


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

if __name__ == '__main__':

    global_data = {}
    root = Path('pickled')
    for d_problem in [p_problem
                      for p_problem in root.iterdir()
                      if p_problem.is_dir()]:
        for d_algorithm in [p_algo
                            for p_algo in d_problem.iterdir()
                            if p_algo.is_dir()]:
            for d_testname in [p_testname
                               for p_testname in d_algorithm.iterdir()
                               if p_testname.is_dir()]:
                sd_testname = False

                d_budget = max([p_budget
                                for p_budget in d_testname.iterdir()
                                if p_budget.is_dir()],
                               key=lambda x: int(x.name))

                for metrics_name_long, metrics_name in [("distance_from_pareto", "dst from pareto"),
                                                        ("distribution", "distribution"),
                                                        ("extent", "extent")]:
                    data = []
                    cost = []
                    for results in d_budget.glob(metrics_name_long + "*.pickle"):
                        with results.open(mode="rb") as fh:
                            test_results = pickle.load(fh)
                            data.append(test_results["metrics"])
                    len_data = len(data)

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
                plt.ylabel(metric, fontsize=15)
                plt.xticks(range(1, len(algos) + 1), [algos[a][0] for a in algos_order], rotation=20)
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




