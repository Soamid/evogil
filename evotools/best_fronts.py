from collections import defaultdict
from pathlib import Path
from contextlib import suppress

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

from evotools import ea_utils
from evotools import metrics

from evotools.pictures import algos, algos_order
from evotools.serialization import RunResult, RESULTS_DIR
from evotools.stats_bootstrap import validate_cost, find_acceptable_result_for_budget

PLOTS_DIR = Path('plots')
PF_PLOTS_DIR = Path('fronts')

metrics_name_long = "distance_from_pareto"

algo_names = [algos[a][0] for a in algos_order]

nondom_colors = {'hgs' : '#d7301f', 'imga' : '#fc8d59', 'bare':'#fdcc8a'}


def plot_problem_front(original_front, multimodal=False, scatter=False):
    f = plt.figure(num=None, facecolor='w', edgecolor='k', figsize=(15, 7))
    ax = Axes3D(f) if len(original_front[0]) > 2 else plt.subplot(111)
    plt.xlabel('1st objective', fontsize=25)
    plt.ylabel("2nd objective", fontsize=30)

    plt.tick_params(axis='both', labelsize=25)

    plt.axhline(linestyle='--', lw=0.9, c='#7F7F7F')
    plt.axvline(linestyle='--', lw=0.9, c='#7F7F7F')

    if len(original_front[0]) == 2:
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

    if len(series[0]) > 2:
        z = [x[2] for x in series]
        f.azim = 60
        f.scatter(x, y, z, c='0.6', s=60, zorder=1)
    f.plot(x, y, c='0.6', lw=6, zorder=1)

def plot_nondom(nondominated):
    f = plt.figure(num=None, facecolor='w', edgecolor='k', figsize=(15, 7))
    ax = plt.subplot(111)

    res_x = [x[0] for x in nondominated]
    res_y = [x[1] for x in nondominated]

    ax.scatter(res_x, res_y, s=60, color='r', zorder=2)
    plt.show()
    # plt.savefig(str('nondom.pdf'))
    # plt.close(f)


def resolve_nondom_color(algo_name):
    if algo_name.startswith('HGS'):
        return nondom_colors['hgs']
    elif algo_name.startswith('IMGA'):
        return nondom_colors['imga']
    else:
        return nondom_colors['bare']

def plot_results(f, best_result, best_result_name, nondominated=set()):
    name, _, markers, color = algos[best_result_name]

    res_x = [x[0] for x in best_result.fitnesses if tuple(x) not in nondominated]
    res_y = [x[1] for x in best_result.fitnesses if tuple(x) not in nondominated]

    res_x_nondom = [x[0] for x in best_result.fitnesses if tuple(x) in nondominated]
    res_y_nondom = [x[1] for x in best_result.fitnesses if tuple(x) in nondominated]

    nondom_c = resolve_nondom_color(best_result_name)

    if len(best_result.fitnesses[0]) > 2:
        res_z = [x[2] for x in best_result.fitnesses if tuple(x) not in nondominated]
        res_z_nondom = [x[2] for x in best_result.fitnesses if tuple(x)  in nondominated]
        f.scatter(res_x, res_y, res_z, marker=markers, s=60, color=color, label=name, zorder=2)
        f.scatter(res_x_nondom, res_y_nondom, res_z_nondom, marker=markers, s=60, color=nondom_c, label=name, zorder=2)
    else:
        f.scatter(res_x, res_y, marker=markers, s=60, color=color, label=name, zorder=2)
        f.scatter(res_x_nondom, res_y_nondom, marker=markers, s=60, color=nondom_c, label=name, zorder=2)


def save_plot(ax, f, d_problem):
    box = ax.get_position()
    # ax.set_position([box.x0, box.y0, box.width * 0.80, box.height])
    handles, labels = ax.get_legend_handles_labels()

    handle_d = dict(zip(labels, handles))
    handles_order = [handle_d[l] for l in algo_names if l in handle_d]
    # plt.legend(handles_order, algo_names, loc='center left', bbox_to_anchor=(1, 0.5), prop={'size': 20}, frameon=False)

    path_pdf =get_path('pdf', d_problem)
    path_eps =get_path('eps', d_problem)
    with suppress(FileExistsError):
        path_pdf.parent.mkdir(parents=True)

    plt.savefig(str(path_pdf), bbox_inches='tight')
    plt.savefig(str(path_eps), bbox_inches='tight')
    plt.close(f)

def get_path(ext, problem_name):
    return Path(PLOTS_DIR) / PF_PLOTS_DIR / 'figures_metrics_{}.{}'.format(problem_name.name.replace('emoa', 'moea'), ext)

def best_fronts_color_nondom(args, queue):
    boot_size = int(args['--bootstrap'])
    scoring = defaultdict(list)
    global_scoring = defaultdict(list)
    for problem_name, problem_mod, algorithms in RunResult.each_result(RESULTS_DIR):
        for algo_name, results in algorithms:
            best_result = find_acceptable_result_for_budget(list(results), boot_size)
            """:type: RunResultBudget """

            if best_result:
                best_value = best_result['results'][0]
                scoring[problem_name, problem_mod].append((algo_name, best_value))
                global_scoring[problem_name].extend(tuple(v) for v in best_value.fitnesses)

    for problem_name in set(global_scoring):
        global_scoring[problem_name] = metrics.filter_not_dominated(global_scoring[problem_name])



    for problem_name, problem_mod in scoring:
        ax, f = plot_problem_front(problem_mod.pareto_front, multimodal=problem_name == 'ZDT3')
        for algo_name,best_value in scoring[(problem_name, problem_mod)]:
            plot_results(ax, best_value, algo_name, global_scoring[problem_name])
        save_plot(ax, f, problem_mod)


def best_fronts(args, queue):
    boot_size = int(args['--bootstrap'])
    for problem_name, problem_mod, algorithms in RunResult.each_result(RESULTS_DIR):
        if problem_name in ['ZDT1', 'ZDT2', 'ZDT3','ZDT4','ZDT6']:
            original_front = problem_mod.pareto_front
            ax, f = plot_problem_front(original_front, multimodal=problem_name == 'ZDT3')

            for algo_name, results in algorithms:
                best_result = find_acceptable_result_for_budget(list(results), boot_size)
                """:type: RunResultBudget """

                if best_result:
                    plot_results(ax, best_result['results'][0], algo_name)
            save_plot(ax, f, problem_mod)


