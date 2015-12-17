import collections
import logging

from evotools.serialization import RunResult, RESULTS_DIR
from evotools.stats_bootstrap import yield_analysis, validate_cost, find_acceptable_result_for_budget
from evotools.timing import log_time, process_time

DEFAULT_TOLERANCE = 0.05
winner_tolerance = {'hypervolume': 0.005, 'igd': DEFAULT_TOLERANCE, 'avd': DEFAULT_TOLERANCE, 'spacing': DEFAULT_TOLERANCE, 'gd': DEFAULT_TOLERANCE, 'pdi': 0.005 }

metrics_order = ['avd', 'gd', 'igd', 'hypervolume', 'pdi', 'spacing']

best_func = {'hypervolume': max, 'igd': min, 'avd': min, 'spacing': min, 'gd': min, 'pdi': max}

result_dirs = ['./results_k0', './results_k1', './results_k2']


def get_weak_winners(scoring, winner, error_rate):
    return [(algo, score) for algo, score in scoring if algo != winner[0] and min(score, winner[1]) / max(score, winner[1]) >= (1-error_rate)]


def table_rank(args, queue):
    logger = logging.getLogger(__name__)
    logger.debug("table ranking")

    boot_size = int(args['--bootstrap'])

    results = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))

    for result_set in result_dirs:
        print("***{}***".format(result_set))
        with log_time(process_time, logger, "Preparing data done in {time_res:.3f}"):
            for problem_name, problem_mod, algorithms in RunResult.each_result(result_set):
                print(result_set, problem_name)
                scoring = collections.defaultdict(list)
                for algo_name, results_data in algorithms:
                    results_data = list(results_data)

                    for i in range(len(results_data)):
                        original_budget = results_data[i]['budget']
                        result = find_acceptable_result_for_budget(results_data[:i+1], boot_size)
                        if result:
                            print("{} {} {} -> {}".format(problem_name, algo_name, original_budget, result['budget']))
                            for metric_name, metric_name_long, data_process in result["analysis"]:
                                if metric_name in best_func:
                                    data_process = list(x() for x in data_process)
                                    data_analysis = yield_analysis(data_process, boot_size)

                                    score = data_analysis["btstrpd"]["metrics"]
                                    scoring[(original_budget, metric_name)].append((algo_name, score))
                print('****{}****'.format(problem_name))
                for budget, metric_name in sorted(scoring):
                    metric_scoring = scoring[(budget, metric_name)]
                    algo_win, score = best_func[metric_name](metric_scoring, key=lambda x: x[1])
                    weak_winners = get_weak_winners(metric_scoring, (algo_win, score), winner_tolerance[metric_name])

                    # Only strong
                    if not weak_winners:
                        results[(budget, metric_name)][result_set].update([algo_win])

                    # Strong = 2 points, Weak or Winner = 1 point
                    # if not weak_winners:
                    #     results[(budget, metric_name)][result_set].update([algo_win, algo_win])
                    # else:
                    #     results[(budget, metric_name)][result_set].update([algo_win] + [algo for algo, score in weak_winners])

                    # print('{} {} {}'.format(budget, metric_name, scoring[(budget, metric_name)]))
                    print('*****{} {}'.format(budget, metric_name))
                    if not weak_winners:
                        print('*****Strong winner: {} :{}'.format(algo_win, score))
                    else:
                        print('*****Winner: {} :{}'.format(algo_win, score))
                        print('*****Weak winners: {}'.format(weak_winners))

    print("""\\begin{table}[ht]
  \\centering
    \\caption{Final results}
    \\label{tab:results"}
    \\resizebox{\\textwidth}{!}{%
    \\begin{tabular}{  r@{ }l | c | c | c | }
          \multicolumn{2}{c}{}
        & $K_0$
        & $K_1$
        & $K_2$
      \\\\ \\hline""")

    prevous_budget = None
    for budget, metric_name in sorted(sorted(results.keys(), key=lambda x: metrics_order.index(x[1])), key=lambda x : x[0]):
        budget_label = str(budget) + ' '
        if prevous_budget and prevous_budget != budget:
            print("\\hdashline")
        elif prevous_budget:
            budget_label = ''

        score_str = ''
        for result_set in result_dirs:
            results_counter = results[(budget, metric_name)][result_set]
            algo_ranking = results_counter.most_common(2)
            values = list(results_counter.values())
            if len(algo_ranking) == 2:
                winner = format_result(algo_ranking[0], values, 2)
                second = format_result(algo_ranking[1], values, 1 if algo_ranking[0][1] != algo_ranking[1][1] else 2)
                score_str += '& {}, {}'.format(winner, second).replace("RHGS", "HGS")
            elif len(algo_ranking) == 1:
                winner = format_result(algo_ranking[0], values, 2)
                score_str += '& {}'.format(winner).replace("RHGS", "HGS")
            else:
                score_str += '& '
        print("{}& {} {}\\\\".format(budget_label, metric_name, score_str))
        prevous_budget = budget

    print("""    \\end{tabular}}\n\\end{table}""")

def format_result(algo_score, results, count):
    return "{} ({})".format(algo_score[0], algo_score[1]) + ("$^*$" if results.count(algo_score[1]) > count else "")


def detailed_rank(args, queue):
    # plot_pareto_fronts()

    logger = logging.getLogger(__name__)
    logger.debug("detailed ranking")

    boot_size = int(args['--bootstrap'])

    for result_set in result_dirs:
        print('***{}***'.format(result_set))
        scoring = collections.defaultdict(list)

        with log_time(process_time, logger, "Preparing data done in {time_res:.3f}"):
            for problem_name, problem_mod, algorithms in RunResult.each_result(result_set):
                for algo_name, results in algorithms:
                    for result in results:
                        if validate_cost(result, boot_size):
                            for metric_name, metric_name_long, data_process in result["analysis"]:
                                if metric_name in best_func:
                                    data_process = list(x() for x in data_process)
                                    data_analysis = yield_analysis(data_process, boot_size)

                                    score = data_analysis["btstrpd"]["metrics"]
                                    scoring[(problem_name, result['budget'], metric_name)].append((algo_name, score))

        global_scoring = collections.defaultdict(collections.Counter)


        for problem_name, budget, metric_name in scoring:
            algo_win, score = best_func[metric_name](scoring[(problem_name, budget, metric_name)], key=lambda x: x[1])
            global_scoring[(budget, metric_name)].update([algo_win])


        for budget, metric_name in sorted(global_scoring):
            print("{} {} : ".format(budget, metric_name) + ", ".join(
            "{} ({})".format(score[0], score[1]) for score in global_scoring[(budget, metric_name)].most_common()))


def rank(args, queue):
    # plot_pareto_fronts()

    logger = logging.getLogger(__name__)
    logger.debug("ranking")

    boot_size = int(args['--bootstrap'])

    scoring = collections.defaultdict(list)

    with log_time(process_time, logger, "Preparing data done in {time_res:.3f}"):
        for problem_name, problem_mod, algorithms in RunResult.each_result(RESULTS_DIR):
            for algo_name,results in algorithms:
                max_budget_result = list(results)[-1]
                if validate_cost(max_budget_result, boot_size):
                    for metric_name, metric_name_long, data_process in max_budget_result["analysis"]:
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
        print("{} : ".format(metric_name) + ", ".join(
            "{} ({})".format(score[0], score[1]) for score in global_scoring[metric_name].most_common()))

