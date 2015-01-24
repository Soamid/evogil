import os
import pickle

import matplotlib.pyplot as plt
from pathlib import Path

from ep.utils import ea_utils
from pictures_from_stats_new import algos


PLOTS_DIR = 'plots'
RESULTS_DIR = 'pareto_results'

metrics_name_long = "distance_from_pareto"


def plot_problem_front(original_front, multimodal=False, scatter=False):
    f = plt.figure(num=None, facecolor='w', edgecolor='k')

    plt.xlabel('1st objective', fontsize=20)
    plt.ylabel("2nd objective", fontsize=20)

    plt.axhline(linestyle='--', lw=0.9, c='#7F7F7F')
    plt.axvline(linestyle='--', lw=0.9, c='#7F7F7F')

    plt.margins(y=.1, x=.1)

    if multimodal:
        subfronts = ea_utils.split_front(original_front, 0.05)
        for front in subfronts:
            plot_front(front, scatter)
    else:
        plot_front(original_front, scatter)

    return f


def plot_front(series, scatter=False):
    x = [x[0] for x in series]
    y = [x[1] for x in series]
    plt.plot(x, y, c='k', lw=6, alpha=0.6)


def plot_results(f, best_result):
    name, _, markers, color = algos[best_result['algorithm']]

    res_x = [x[0] for x in best_result['result']]
    res_y = [x[1] for x in best_result['result']]
    plt.scatter(res_x, res_y, marker=markers, color=color)


def save_plot(f):
    os.makedirs(PLOTS_DIR, exist_ok=True)
    os.makedirs(os.path.join(PLOTS_DIR, RESULTS_DIR), exist_ok=True)

    fig_path = os.path.join(PLOTS_DIR, RESULTS_DIR, '{}.eps'.format(d_problem.name.replace('emoa', 'moea')))
    plt.savefig(fig_path)
    plt.close(f)


if __name__ == '__main__':

    global_data = {}
    root = Path('pickled')
    for d_problem in [p_problem
                      for p_problem in root.iterdir()
                      if p_problem.is_dir()]:


        problem_mod = __import__('problems.{}.problem'.format(d_problem.name), fromlist=[d_problem.name])
        original_front = problem_mod.pareto_front
        f = plot_problem_front(original_front, multimodal=d_problem.name == 'coemoa_c', scatter=d_problem.name == 'ackley')

        for d_algorithm in [p_algo
                            for p_algo in d_problem.iterdir()
                            if p_algo.is_dir()]:

            best_result = None

            for d_testname in [p_testname
                               for p_testname in d_algorithm.iterdir()
                               if p_testname.is_dir()]:
                sd_testname = False

                d_budget = max([p_budget
                                for p_budget in d_testname.iterdir()
                                if p_budget.is_dir()],
                               key=lambda x: int(x.name))

                for results in d_budget.glob(metrics_name_long + "*.pickle"):
                    with results.open(mode="rb") as fh:
                        test_results = pickle.load(fh)
                        if not best_result or test_results["metrics"] < best_result["metrics"]:
                            best_result = test_results

            plot_results(f, best_result)

        save_plot(f)

