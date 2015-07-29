import logging
import collections
from evotools.serialization import RunResult
from evotools.stats_bootstrap import yield_analysis
from evotools.timing import log_time, process_time

best_func = { 'hypervolume' : max, 'igd' : min, 'ndr' : max, 'spacing' : min, 'extent' : max, 'gd' : min, 'epsilon' : max}


def table_rank(args, queue):
    logger = logging.getLogger(__name__)
    logger.debug("table ranking")

    boot_size = int(args['--bootstrap'])

    result_dirs = ['results0', 'results1', 'results2']

    results = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))

    for result_set in result_dirs:
        with log_time(process_time, logger, "Preparing data done in {time_res:.3f}"):
            for problem_name, problem_mod, algorithms in RunResult.each_result(result_set):
                print(result_set, problem_name)
                scoring = collections.defaultdict(list)
                for algo_name, budgets in algorithms:
                    for budget in budgets:
                        for metric_name, metric_name_long, data_process in budget["analysis"]:
                            if metric_name in best_func:
                                data_process = list(x() for x in data_process)
                                data_analysis = yield_analysis(data_process, boot_size)

                                score = data_analysis["btstrpd"]["metrics"]
                                scoring[(budget['budget'], metric_name)].append((algo_name, score))

                for budget, metric_name in scoring:
                    algo_win, score = best_func[metric_name](scoring[(budget, metric_name)], key=lambda x: x[1])
                    results[(budget, metric_name)][result_set].update([algo_win])

    print("""\\begin{table}[ht]
  \\centering
    \\caption{Final results}
    \\label{tab:results"}
    \\begin{tabular}{  c | r@{.}l : r@{.}l : r@{.}l }
        & results0
        & results1
        & results3
      \\\\ \\hline""")

    for budget, metric_name in sorted(results.keys(), key=lambda x : x[0]):
        score_str = ''
        for result_set in result_dirs:
            algo_name, score = results[(budget, metric_name)][result_set].most_common(1)[0]
            score_str += '& {} ({}) '.format(algo_name, score)
        print("{} {} {}\\\\".format(budget, metric_name, score_str))

    print("""    \\end{tabular}\n\\end{table}""")




def rank(args, queue):
    # plot_pareto_fronts()

    logger = logging.getLogger(__name__)
    logger.debug("ranking")

    boot_size = int(args['--bootstrap'])

    scoring = collections.defaultdict(list)

    with log_time(process_time, logger, "Preparing data done in {time_res:.3f}"):
        for problem_name, problem_mod, algorithms in RunResult.each_result():
            for algo_name, budgets in algorithms:
                max_budget = list(budgets)[4]
                for metric_name, metric_name_long, data_process in max_budget["analysis"]:
                    if metric_name in best_func:
                        data_process = list(x() for x in data_process)
                        data_analysis = yield_analysis(data_process, boot_size)

                        score = data_analysis["btstrpd"]["metrics"]
                        scoring[(problem_name, metric_name)].append((algo_name, score))

    global_scoring = collections.defaultdict(collections.Counter)

    print("Problem ranking\n################")
    for problem_name, metric_name in scoring:
        algo_win, score = best_func[metric_name](scoring[(problem_name, metric_name)], key=lambda x: x[1])
        print("{}, {} : {}".format(problem_name, metric_name, algo_win))
        global_scoring[metric_name].update([algo_win])

    print("\nGlobal ranking\n##############")
    for metric_name in global_scoring:
        print("{} : ".format(metric_name) + ", ".join("{} ({})".format(score[0], score[1]) for score in global_scoring[metric_name].most_common()))

