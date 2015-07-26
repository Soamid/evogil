import collections
import logging
from contextlib import suppress
from pathlib import Path

from evotools import ea_utils
from evotools.serialization import RunResult, evotools
from evotools.stats_bootstrap import yield_analysis
from evotools.timing import log_time, process_time
from evotools import ranking
import problems.ackley.problem as ackley
import problems.ZDT1.problem as zdt1
import problems.ZDT2.problem as zdt2
import problems.ZDT3.problem as zdt3
import problems.ZDT4.problem as zdt4
import problems.ZDT6.problem as zdt6


PLOTS_DIR = Path('plots')

import matplotlib

matplotlib.rcParams.update({'font.size': 8})
import matplotlib.pyplot as plt

SPEA_LS = []  # '-'
NSGAII_LS = [10, 2]  # '--'
NSGAIII_LS = [30, 2]  # '-- --'
IBEA_LS = [2, 2]  # '.....'
OMOPSO_LS = [10, 2, 5, 2]  # '-.'
SMSEMOA_LS = [2, 10]  # ':  :  :'

SPEA_M = 'o'
NSGAII_M = '*'
IBEA_M = '^'
OMOPSO_M = '>'
NSGAIII_M = 'v'
SMSEMOA_M = '<'

BARE_CL = '0.8'
IMGA_CL = '0.4'
RHGS_CL = '0.0'

algos = {'SPEA2': ('SPEA2', SPEA_LS, SPEA_M, BARE_CL),
         'NSGAII': ('NSGAII', NSGAII_LS, NSGAII_M, BARE_CL),
         'IBEA': ( 'IBEA', IBEA_LS, IBEA_M, BARE_CL),
         'OMOPSO': ('OMOPSO', OMOPSO_LS, OMOPSO_M, BARE_CL),
         'NSGAIII': ('NSGAIII', NSGAIII_LS, NSGAIII_M, BARE_CL),
         'SMSEMOA': ('SMSEMOA', SMSEMOA_LS, SMSEMOA_M, BARE_CL),

         'IMGA+SPEA2': ('IMGA+SPEA2', SPEA_LS, SPEA_M, IMGA_CL),
         'IMGA+NSGAII': ( 'IMGA+NSGAII', NSGAII_LS, NSGAII_M, IMGA_CL),
         'IMGA+OMOPSO': ('IMGA+OMOPSO', OMOPSO_LS, OMOPSO_M, IMGA_CL),
         'IMGA+IBEA': ('IMGA+IBEA', IBEA_LS, IBEA_M, IMGA_CL),
         'IMGA+NSGAIII': ( 'IMGA+NSGAIII', NSGAIII_LS, NSGAIII_M, IMGA_CL),
         'IMGA+SMSEMOA': ( 'IMGA+SMSEMOA', SMSEMOA_LS, SMSEMOA_M, IMGA_CL),

         'RHGS+SPEA2': ( 'RHGS+SPEA2', SPEA_LS, SPEA_M, RHGS_CL),
         'RHGS+NSGAII': ( 'RHGS+NSGAII', NSGAII_LS, NSGAII_M, RHGS_CL),
         'RHGS+IBEA': ( 'RHGS+IBEA', IBEA_LS, IBEA_M, RHGS_CL),
         'RHGS+OMOPSO': ('RHGS+OMOPSO', OMOPSO_LS, OMOPSO_M, RHGS_CL),
         'RHGS+NSGAIII': ( 'RHGS+NSGAIII', NSGAIII_LS, NSGAIII_M, RHGS_CL),
         'RHGS+SMSEMOA': ( 'RHGS+SMSEMOA', SMSEMOA_LS, SMSEMOA_M, RHGS_CL),
         }

algos_order = [
    'SPEA2', 'NSGAII', 'IBEA', 'OMOPSO', 'NSGAIII', 'SMSEMOA',
    'IMGA+SPEA2', 'IMGA+NSGAII', 'IMGA+IBEA', 'IMGA+OMOPSO', 'IMGA+NSGAIII', 'IMGA+SMSEMOA',
    'RHGS+SPEA2', 'RHGS+NSGAII', 'RHGS+IBEA', 'RHGS+OMOPSO', 'RHGS+NSGAIII', 'RHGS+SMSEMOA',
]

algos_groups_configuration_all_together = {
    ('SPEA2', 'NSGAII', 'IBEA', 'OMOPSO', 'NSGAIII', 'SMSEMOA',
     'IMGA+SPEA2', 'IMGA+NSGAII', 'IMGA+IBEA', 'IMGA+OMOPSO', 'IMGA+NSGAIII', 'IMGA+SMSEMOA',
     'RHGS+SPEA2', 'RHGS+NSGAII', 'RHGS+IBEA', 'RHGS+OMOPSO', 'RHGS+NSGAIII', 'RHGS+SMSEMOA'): ('',)
}

algos_groups_configuration_splitted = {
    ('SPEA2', 'NSGAII', 'IBEA', 'OMOPSO', 'NSGAIII', 'SMSEMOA'): (0, 1),
    ('IMGA+SPEA2', 'IMGA+NSGAII', 'IMGA+IBEA', 'IMGA+OMOPSO', 'IMGA+NSGAIII', 'IMGA+SMSEMOA'): (0, 2),
    ('RHGS+SPEA2', 'RHGS+NSGAII', 'RHGS+IBEA', 'RHGS+OMOPSO', 'RHGS+NSGAIII', 'RHGS+SMSEMOA'): (1, 2)
}

algos_groups_configuration_tres_caballeros = {
    ('SPEA2', 'IMGA+SPEA2', 'RHGS+SPEA2'): ('_spea2',),
    ('NSGAII', 'IMGA+NSGAII', 'RHGS+NSGAII'): ('_nsgaii',),
    ('IBEA', 'IMGA+IBEA', 'RHGS+IBEA'): ('_ibea',),
    ('NSGAIII', 'IMGA+NSGAIII', 'RHGS+NSGAIII'): ('_nsgaiii',),
    ('SMSEMOA', 'IMGA+SMSEMOA', 'RHGS+SMSEMOA'): ('_smsemoa',),
    ('OMOPSO', 'IMGA+OMOPSO', 'RHGS+OMOPSO'): ('_omopso',),
}

problems_order = ['ZDT1', 'ZDT2', 'ZDT3', 'ZDT4', 'ZDT6', 'UF1', 'UF2', 'UF3', 'UF4', 'UF5', 'UF6', 'UF7', 'UF8', 'UF9',
                  'UF10', 'UF11', 'UF12']

algos_groups_configuration = algos_groups_configuration_tres_caballeros

algos_groups = {a: group for algorithms, group in algos_groups_configuration.items() for a in algorithms}


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
        plt.scatter(prto_x, prto_y, c='k', s=300, edgecolors='none')
    else:
        plt.margins(y=.1, x=.1)
        plt.plot(prto_x, prto_y, 'k-', lw=6)

    frame = plt.gca()

    frame.axes.get_xaxis().set_ticklabels([])
    frame.axes.get_yaxis().set_ticklabels([])

    if save:
        path = PLOTS_DIR / 'pareto_fronts' / (name + '.pdf')
        with suppress(FileExistsError):
            path.parent.mkdir(parents=True)
        plt.savefig(str(path))
        plt.close(f)

    return f


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

            get_algo_results(results, "MO-RHGS+SPEA2", "hgs_spea2", metric),
            get_algo_results(results, "MO-RHGS+NSGA-II", "hgs_nsga2", metric),
            get_algo_results(results, "MO-RHGS+IBEA", "hgs_ibea", metric)
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
    # print('{} : {}, dev: {}, n={}'.format(result, rounded, error, round_n))

    return rounded


def plot_legend(series):
    figlegend = plt.figure(num=None, figsize=(8.267 / 2.0, 11.692 / 4.0), facecolor='w', edgecolor='k')

    figlegend.legend(series, [s.get_label() for s in series], 'center', prop={'size': 10},
                     handlelength=8, borderpad=1.2, labelspacing=1, frameon=False)

    path = PLOTS_DIR / 'plots_bnw' / 'legend.eps'
    with suppress(FileExistsError):
        path.parent.mkdir(parents=True)
    figlegend.savefig(str(path))


def plot_results(results):
    logger = logging.getLogger(__name__)
    legend_saved = False
    to_plot = collections.defaultdict(list)
    for key, values in results.items():
        (problem, algo, metric, group) = key
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
        to_plot[(problem, metric, group)].append((algo, ((xs, xerr), (ys, yerr))))

    logger.debug("to_plot = %s", list(to_plot.items()))

    for plot_name, plot_data in to_plot.items():
        last_plt = []
        plt.figure(num=None, facecolor='w', edgecolor='k', figsize=(15, 7))
        ax = plt.subplot(111)
        # plt.title(plot_name)
        (problem, metric, group) = plot_name
        if metric == 'dst':
            metric = 'distance from Pareto front'
            if problem == 'ackley':
                ylim = [0.0001, 10]
                logger.debug("plt.ylim = %s", ylim)
                plt.ylim(ylim)
            plt.yscale('log')
        if metric == 'distribution':
            if problem == 'ackley' or problem == 'ZDT2':
                ylim = [-0.1, 1.0]
                logger.debug("plt.ylim = %s", ylim)
                plt.ylim(ylim)
        if metric == 'extent':
            if problem == 'ackley':
                ylim = [-0.5, 4.0]
                logger.debug("plt.ylim = %s", ylim)
                plt.ylim(ylim)
        logger.debug("plt.ylabel = %s", metric)
        plt.ylabel(metric, fontsize=20)
        plt.xlabel('calls to fitness function', fontsize=20)
        plt.tick_params(axis='both', labelsize=15)
        plot_data = sorted(plot_data, key=lambda x: x[0])
        logger.debug("plot_data = %s", plot_data)
        lw = 5
        base_ms = 5
        plot_data = dict(plot_data)
        logger.debug("plot_data = %s", plot_data)
        for algo in algos_order:
            logger.debug("for algo=%s", algo)
            if algo in plot_data:
                data = plot_data[algo]
                name, lines, marker, color = algos[algo]
                (xs, xerr), (ys, yerr) = data
                if 'NSGAII' in algo:
                    ms = base_ms + 1
                else:
                    ms = base_ms

                last_plt.append(ax.plot(xs, ys, color=color, label=name, linewidth=lw, ms=ms)[0])
                last_plt[-1].set_dashes(lines)

        logger.debug("last_plt = %s", last_plt)
        problem, metric, group = plot_name

        # plt.legend(loc='best', fontsize=6)
        # plt.show()
        # if not legend_saved:
        # plot_legend(last_plt)
        # legend_saved = True

        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.80, box.height])

        plt.legend(last_plt, [s.get_label() for s in last_plt], loc='center left', bbox_to_anchor=(1, 0.5),
                   prop={'size': 20}, frameon=False)

        problem_moea = problem.replace('emoa', 'moea')
        # plt.tight_layout()
        metric_short = metric.replace('distance from Pareto front', 'dst')
        path = PLOTS_DIR / 'plots_bnw' / '{}_{}.pdf'.format(problem_moea, metric_short + str(group))

        with suppress(FileExistsError):
            path.parent.mkdir(parents=True)
        plt.savefig(str(path))
        plt.close()


def pictures_from_stats(args, queue):
    # plot_pareto_fronts()

    logger = logging.getLogger(__name__)
    logger.debug("pictures from stats")

    boot_size = int(args['--bootstrap'])

    results = collections.defaultdict(list)
    with log_time(process_time, logger, "Preparing data done in {time_res:.3f}"):
        for problem_name, problem_mod, algorithms in RunResult.each_result():
            for algo_name, budgets in algorithms:
                for result in budgets:
                    _, _, cost_data = next(result["analysis"])
                    cost_data = list(x() for x in cost_data)
                    cost_analysis = yield_analysis(cost_data, boot_size)

                    budget = cost_analysis["btstrpd"]["metrics"]
                    budget_err = cost_analysis["stdev"]

                    for metric_name, metric_name_long, data_process in result["analysis"]:
                        if metric_name == 'dst from pareto':
                            metric_name = 'dst'
                        data_process = list(x() for x in data_process)

                        data_analysis = yield_analysis(data_process, boot_size)

                        score = data_analysis["btstrpd"]["metrics"]
                        score_err = data_analysis["stdev"]

                        keys = [(problem_name, algo_name, metric_name, group) for group in algos_groups[algo_name]]
                        value = (budget, budget_err, score, score_err)

                        for key in keys:
                            results[key].append(value)

    plot_results(results)


def plot_results_summary(problems, scoring, selected):
    for metric_name in scoring:
        metric_score = scoring[metric_name]

        plt.figure()
        x_axis = range(len(problems))
        problem_labels = [p for p in problems_order if p in problems]
        plt.xticks(x_axis, problem_labels)

        for algo in metric_score:
            name, lines, marker, color = algos[algo]
            x_algo = []
            y_algo = []
            for x in x_axis:
                problem = problem_labels[x]
                if problem in metric_score[algo]:
                    x_algo.append(x)
                    y_algo.append(metric_score[algo][problem])

            print(x_algo, metric_score[algo])

            plt.scatter(x_algo, y_algo, c=color, s=60, marker=marker, label=name)
            if algo in selected:
                ax = plt.plot(x_algo, y_algo, color=color, label=name)
                ax[0].set_dashes(lines)

        path = PLOTS_DIR / 'plots_summary' / '{}.pdf'.format(metric_name)

        with suppress(FileExistsError):
            path.parent.mkdir(parents=True)
        plt.savefig(str(path))
        plt.close()


def pictures_summary(args, queue):
    logger = logging.getLogger(__name__)
    logger.debug("pictures_summary")

    selected = set(args['--selected'].upper().split(','))
    boot_size = int(args['--bootstrap'])

    logger.debug('Plotting summary with selected algos: ' + ','.join(selected))

    scoring = collections.defaultdict(lambda: collections.defaultdict(dict))
    problems = set()

    with log_time(process_time, logger, "Preparing data done in {time_res:.3f}"):
        for problem_name, problem_mod, algorithms in RunResult.each_result():
            problems.add(problem_name)
            problem_score = collections.defaultdict(list)
            algos = list(algorithms)
            for algo_name, budgets in algos:
                max_budget = list(budgets)[-1]
                for metric_name, metric_name_long, data_process in max_budget["analysis"]:
                    if metric_name in ranking.best_func:
                        data_process = list(x() for x in data_process)
                        data_analysis = yield_analysis(data_process, boot_size)

                        score = data_analysis["btstrpd"]["metrics"]

                        scoring[metric_name][algo_name][problem_name] = score
                        problem_score[metric_name].append(score)

            for metric_name in scoring:
                max_score = max(problem_score[metric_name]) + 1
                for algo_name, _ in algos:
                    if algo_name in scoring[metric_name]:
                        scoring[metric_name][algo_name][problem_name] /= max_score

    plot_results_summary(problems, scoring, selected)

