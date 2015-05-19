import json

import matplotlib.pyplot as plt
from pathlib import Path

from evotools import ea_utils
from evotools.pictures import algos, algos_order

from contextlib import suppress

PLOTS_DIR = Path('plots')
RESULTS_DIR = Path('pareto_results')

metrics_name_long = "distance_from_pareto"

algo_names = [algos[a][0] for a in algos_order]


def plot_problem_front(original_front, multimodal=False, scatter=False):
    f = plt.figure(num=None, facecolor='w', edgecolor='k', figsize=(15, 7))
    ax = plt.subplot(111)

    plt.xlabel('1st objective', fontsize=20)
    plt.ylabel("2nd objective", fontsize=20)

    plt.tick_params(axis='both',  labelsize=15)

    plt.axhline(linestyle='--', lw=0.9, c='#7F7F7F')
    plt.axvline(linestyle='--', lw=0.9, c='#7F7F7F')

    plt.margins(y=.1, x=.1)

    if multimodal:
        subfronts = ea_utils.split_front(original_front, 0.05)
        for front in subfronts:
            plot_front(ax, front, scatter)
    else:
        plot_front(ax, original_front, scatter)

    return ax, f


def plot_front(f, series, scatter=False):
    x = [x[0] for x in series]
    y = [x[1] for x in series]
    f.plot(x, y, c='0.6', lw=6, zorder=1)


def plot_results(f, best_result):
    name, _, markers, color = algos[best_result['algorithm']]

    res_x = [x[0] for x in best_result['result']]
    res_y = [x[1] for x in best_result['result']]
    f.scatter(res_x, res_y, marker=markers, s=60, color=color,  label=name, zorder=2)
    # f.scatter(res_x, res_y, marker=markers, s=60, edgecolors=color, facecolors='none', label=name, zorder=2)


def save_plot(ax, f, d_problem):
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.80, box.height])
    handles, labels = ax.get_legend_handles_labels()


    handle_d =  dict(zip(labels, handles))
    handles_order = [handle_d[l] for l in algo_names if l in handle_d]

    plt.legend(handles_order, algo_names, loc='center left', bbox_to_anchor=(1, 0.5), prop={'size': 20}, frameon=False)

    
    path = Path(PLOTS_DIR) / RESULTS_DIR / '{}.eps'.format(d_problem.name.replace('emoa', 'moea'))
    with suppress(FileExistsError):
        path.parent.mkdir(parents=True)

    plt.savefig(str(path))
    plt.close(f)


def main():

    global_data = {}
    root = Path('jsoned')
    for d_problem in [p_problem
                      for p_problem in root.iterdir()
                      if p_problem.is_dir()]:


        problem_mod = __import__('problems.{}.problem'.format(d_problem.name), fromlist=[d_problem.name])
        original_front = problem_mod.pareto_front
        ax, f = plot_problem_front(original_front, multimodal=d_problem.name == 'ZDT3', scatter=d_problem.name == 'ackley')

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

                for results in d_budget.glob(metrics_name_long + "*.json"):
                    with results.open(mode="r") as fh:
                        test_results = json.load(fh)
                        if not best_result or test_results["metrics"] < best_result["metrics"]:
                            best_result = test_results

            plot_results(ax, best_result)

        save_plot(ax, f, d_problem)

