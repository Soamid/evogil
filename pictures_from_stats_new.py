import collections
import os

import matplotlib

from algorithms.utils import ea_utils
import problems.ackley.problem as ackley
import problems.ZDT1.problem as zdt1
import problems.ZDT2.problem as zdt2
import problems.ZDT3.problem as zdt3
import problems.ZDT4.problem as zdt4
import problems.ZDT6.problem as zdt6


PLOTS_DIR = 'plots'

matplotlib.rcParams.update({'font.size': 8})
import matplotlib.pyplot as plt

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


def plot_pareto_fronts():
    problems = [(zdt1, 'ZDT1'), (zdt2, 'ZDT2'), (zdt4, 'ZDT4'), (zdt6, 'ZDT6')]

    for problem in problems:
        problem, name = problem
        pareto_front = problem.pareto_front
        plot_front(pareto_front, name)

    plot_front(ackley.pareto_front, 'Ackley', scattered=True)

    zdt3_front = zdt3.pareto_front
    fronts = ea_utils.split_front(zdt3_front, 0.05)
    fig = None
    for front in fronts[:-1]:
        fig = plot_front(front, None, figure=fig, save=False)

    plot_front(fronts[-1], 'ZDT3', figure=fig, save=True)


def plot_front(pareto_front, name, scattered=False, figure=None, save=True):
    if figure:
        f = figure
    else:
        f = plt.figure()
    plt.axhline(linestyle='--', lw=0.9, c='#7F7F7F')
    plt.axvline(linestyle='--', lw=0.9, c='#7F7F7F')

    prto_x = [x[0] for x in pareto_front]
    prto_y = [x[1] for x in pareto_front]

    if scattered:
        plt.scatter(prto_x, prto_y, c='k', s=300,  edgecolors='none')
    else:
        plt.margins(y=.1, x=.1)
        plt.plot(prto_x, prto_y, 'k-', lw=6)

    frame = plt.gca()

    frame.axes.get_xaxis().set_ticklabels([])
    frame.axes.get_yaxis().set_ticklabels([])

    if save:
        plt.savefig(os.path.join(PLOTS_DIR, 'pareto_fronts', name + '.pdf'))
        plt.close(f)

    return f


def parse_stats(stats_file):
    stats_lines = []
    with open(stats_file, encoding="utf8") as f:
        for line in f.readlines():
            stats_lines.append(line)

    results = collections.defaultdict(list)

    algo = None
    budget = None
    metric = None
    planned = None
    for line in stats_lines:
        if line[0] == '[' or line[0] == '=' or line[0] == '#' or line[0] == '>':
            continue
        parts = [x.strip() for x in line.split("::")]
        if parts[0] == '':
            continue
        if not parts[4] == '':
            planned = int(parts[4])
        problem = parts[0]
        if not parts[1] == '':
            algo = parts[1]
        if not parts[5] == '':
            metric = parts[5]
        if metric == 'dst from pareto':
            metric = 'dst'
        if planned == 0:
            continue
        key = (problem, algo, metric)
        score = [float(x) for x in parts[7].split('≤')][1]
        score_err = float(parts[8])
        budget = [float(x) for x in parts[15].split('≤')][1]
        budget_err = float(parts[16])
        results[key].append((budget, budget_err, score, score_err))

    return results


def tex_align_floats(*xs):
    """To align columns, we place '&' instead of dot in floats."""
    return [str(x).replace('.', '&') for x in xs]


def tex_align_floats_winner(x):
    """To align and boldify the float, use `\\newcommand{\\tb}[2]{\\textbf{#1}&\\textbf{#2}}`
    so to translate 123.456 --> \tb{123}{456}"""
    return "\\tb{" + str(x).replace('.', '}{') + "}"


def gen_table(results):
    metrics = {"dst": ("Distance from Pareto front", min), "distribution": ("Distribution", max),
               "extent": ("Extent", max)}
    for metric in metrics:
        print("""\\begin{table}[ht]
  \\centering
    \\caption{Final results: the \\emph{""" + metrics[metric][0] + """} metric.}
    \\label{tab:results:""" + metric + """}
    \\begin{tabular}{  c | r@{.}l : r@{.}l : r@{.}l : r@{.}l : r@{.}l : r@{.}l }
        & \\multicolumn{2}{|c|}{Ackley}
        & \\multicolumn{2}{|c|}{ZDT1}
        & \\multicolumn{2}{|c|}{ZDT2}
        & \\multicolumn{2}{|c|}{ZDT3}
        & \\multicolumn{2}{|c|}{ZDT4}
        & \\multicolumn{2}{|c}{ZDT6} 
      \\\\ \\hline""")
        printable_results = [
            get_algo_results(results, "SPEA2", "spea2", metric),
            get_algo_results(results, "NSGA-II", "nsga2", metric),
            get_algo_results(results, "IBEA", "ibea", metric),

            get_algo_results(results, "IMGA+SPEA2", "imga_spea2", metric),
            get_algo_results(results, "IMGA+NSGA-II", "imga_nsga2", metric),
            get_algo_results(results, "IMGA+IBEA", "imga_ibea", metric),

            get_algo_results(results, "MO-HGS+SPEA2", "hgs_spea2", metric),
            get_algo_results(results, "MO-HGS+NSGA-II", "hgs_nsga2", metric),
            get_algo_results(results, "MO-HGS+IBEA", "hgs_ibea", metric)
        ]
        mark_winner(printable_results, metrics[metric][1])

        for res in printable_results:
            print("\t\t\t{:16} & {:11} & {:11} & {:11} & {:11} & {:11} & {:11} \\\\".format(res[0], *tex_align_floats(
                *res[1:])))
            if res[0] in ["IBEA", "IMGA+IBEA"]:
                print("\t\t\\hdashline")

        print("""    \\end{tabular}\n\\end{table}""")


def get_algo_results(results, algo_display, algo, metric):
    return [algo_display,
            get_last(results, "ackley", algo, metric),
            get_last(results, "ZDT1", algo, metric),
            get_last(results, "ZDT2", algo, metric),
            get_last(results, "ZDT3", algo, metric),
            get_last(results, "ZDT4", algo, metric),
            get_last(results, "ZDT6", algo, metric)]


def mark_winner(printable_results, marker_func):
    for i in range(1, len(printable_results[0])):
        algo_results = [float(val[i]) for val in printable_results]
        winner_val = marker_func(algo_results)
        winner_indexes = [i for i, j in enumerate(algo_results) if j == winner_val]
        for index in winner_indexes:
            str(winner_val)
            printable_results[index][i] = tex_align_floats_winner(winner_val)


def get_last(results, problem, algo, metric):
    if not results[(problem, algo, metric)]:
        return None
    else:
        _, _, score, error = results[(problem, algo, metric)][-1]
        return align_to_error(score, error)


def align_to_error(result, error):

    if error == 0.0:
        return result
    error = str(error)

    dot_pos = error.find('.')
    non_zero_pos = 0
    for i in range(len(error)):
        if error[i] == '.':
            non_zero_pos -= 1
        elif error[i] != '0':
            non_zero_pos = i
            break

    diff = 1
    if len(error) > non_zero_pos + diff and error[non_zero_pos + diff] == '.':
        diff += 1
    pos = non_zero_pos + diff

    if len(error) < pos + 1 or error[pos] == '0':
        pos -= diff

    round_n = pos - dot_pos
    if round_n < 0:
        round_n = min(round_n + 2, 0)


    rounded = round(result, round_n)

    # if rounded != result:
    #     print('{} : {}, dev: {}, n={}'.format(result, rounded, error, round_n))

    return rounded


def plot_legend(series):
    figlegend = plt.figure(num=None, figsize=(8.267 / 2.0, 11.692 / 4.0), facecolor='w', edgecolor='k')

    figlegend.legend(series, [s.get_label() for s in series], 'center', prop={'size': 10},
                     handlelength=8, borderpad=1.2, labelspacing=1, frameon=False)

    figlegend.savefig(os.path.join(PLOTS_DIR, 'plots_bnw', 'legend.eps'))


def plot_results(results):
    legend_saved = False
    to_plot = collections.defaultdict(list)
    for key, values in results.items():
        (problem, algo, metric) = key
        xs = []
        xerr = []
        ys = []
        yerr = []
        values = sorted(values, key=lambda x: x[0])
        for b, be, s, se in values:
            xs.append(b)
            xerr.append(be)
            ys.append(s)
            yerr.append(se)
        to_plot[(problem, metric)].append((algo, ((xs, xerr), (ys, yerr))))

    for plot_name, plot_data in to_plot.items():
        last_plt = []
        plt.figure(num=None, facecolor='w', edgecolor='k' , figsize=(15, 7))
        ax = plt.subplot(111)
        # plt.title(plot_name)
        (problem, metric) = plot_name
        if metric == 'dst':
            metric = 'distance from Pareto front'
            if problem == 'ackley':
                plt.ylim([0.0001, 10])
            plt.yscale('log')
        if metric == 'distribution':
            if problem == 'ackley' or problem == 'comoea_b':
                plt.ylim([-0.1, 1.0])
        if metric == 'extent':
            if problem == 'ackley':
                plt.ylim([-0.5, 4.0])
        plt.ylabel(metric, fontsize=20)
        plt.xlabel('calls to fitness function', fontsize=20)
        plt.tick_params(axis='both',  labelsize=15)
        plot_data = sorted(plot_data, key=lambda x: x[0])
        lw = 5
        base_ms = 5
        plot_data = dict(plot_data)
        for algo in algos_order:
            data = plot_data[algo]
            name, lines, marker, color = algos[algo]
            (xs, xerr), (ys, yerr) = data
            if 'nsga2' in algo:
                ms = base_ms + 1
            else:
                ms = base_ms

            last_plt.append(ax.plot(xs, ys, ls=lines, color=color, label=name, linewidth=lw, ms=ms)[0])

        problem, metric = plot_name

        # plt.legend(loc='best', fontsize=6)
        # plt.show()
        # if not legend_saved:
        #     plot_legend(last_plt)
        #     legend_saved = True

        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.80, box.height])

        plt.legend(last_plt, [s.get_label() for s in last_plt], loc='center left', bbox_to_anchor=(1, 0.5), prop={'size': 20}, frameon=False)

        problem_moea = problem.replace('emoa', 'moea')
        # plt.tight_layout()
        metric_short = metric.replace('distance from Pareto front', 'dst')
        path = os.path.join(PLOTS_DIR, 'plots_bnw', '{}_{}.eps'.format(problem_moea, metric_short))
        plt.savefig(path)


if __name__ == '__main__':
    # plot_pareto_fronts()
    stats = parse_stats("stats.txt")
    # gen_table(stats)
    plot_results(stats)
