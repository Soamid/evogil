from contextlib import closing
from functools import partial
from itertools import repeat
import logging
import multiprocessing
from evotools.log_helper import init_worker
from evotools.random_tools import close_and_join
from evotools.serialization import RunResult
from evotools.stats_bootstrap import yield_analysis, average
from evotools.timing import process_time, log_time

fields = [
    ("PROBLEM",                     [9],             "{problem_name:{0}}"),
    ("ALGO",                        [14],            "{algo_name:{0}}"),
    ("N",                           [2],             "{len_data:>{0}}"),
    # ("AvgPop",                      [5],             "{avg_pop_len:{0}}"),
    ("Budgt",                       [5],             "{result[budget]!s:>{0}}"),
    ("METRICS OY",                  [15],            "{metric_name:^{0}}"),
    ("✓",                           [5],             "{analysis[goodbench]:^{0}}"),
    ("RESULT, confidence interval", [10, 10, 10, 6], "{analysis[btstrpd][from]: >0{0}.3f} ≤ {analysis[btstrpd][metrics]: >{1}.3f} ≤ {analysis[btstrpd][to]: >0{2}.3f}"),
    ("σ",                           [10],            "{analysis[stdev]: >{0}.3f}"),
    ("OUTLIERS",                    [7, 7, 12],      "{analysis[mild_outliers]:>{0}} mild {analysis[extr_outliers]:>{1}} extr."),
    ("RES w/o outliers",            [10, 10, 4],     "{analysis[metrics_nooutliers]:>{0}.3f} ({analysis[mean_nooutliers_diff]:>+{1}.3f}%)"),
    ("σ w/o outliers",              [10, 10, 4],     "{analysis[stdev_nooutliers]:>{0}.3f} ({analysis[stdev_nooutliers_diff]:>{1}.3f}%)"),
    ("(C INT)/METRICS",             [7, 10, 2],      "{analysis[pr_dispersion]: >{0}.3f}% {analysis[dispersion_warn]:<{1}}"),
]


def force_data(args):
    boot_size, (metric_name, metric_name_long, data_process) = args

    data_process = list(x() for x in data_process)
    force_analysis = yield_analysis(data_process, boot_size)
    return metric_name, metric_name_long, data_process, force_analysis


def statistics(args, queue):
    logger = logging.getLogger(__name__)

    badbench = []
    cost_badbench = []
    boot_size = int(args['--bootstrap'])

    # pretty format
    screen_width = sum(y for x in fields for y in x[1]) + 4 * len(fields)
    [err_prefix] = [
        i
        for i, (name, lens, fmt) in enumerate(fields)
        if name == "RESULT, confidence interval"
    ]
    err_prefix = sum(y for x in fields[:err_prefix] for y in x[1]) + 4 * err_prefix - 2
    err_prefix = " " * err_prefix

    def print_header():
        print()
        print('..'.join('[{0:^{1}}]'.format(head, sum(width))
                        for head, width, var
                        in fields)
              + "..",
              flush=True)
        return True

    with close_and_join(multiprocessing.Pool(min(int(args['-j']), 8))) as p:
        for problem_name, problem_mod, algorithms in RunResult.each_result():
            for algo_name, budgets in algorithms:
                header_just_printed = print_header()

                for result in budgets:
                    len_data = len(result["results"])

                    first_budget_line = True
                    avg_pop_len = average([len(x.population) for x in result["results"]])

                    with log_time(process_time,
                                  logger,
                                  "Calculating metrics for {} :: {} :: {} in {{time_res:.3f}}s".format(
                                      problem_name, algo_name, result["budget"]
                                  )):

                        results_precalc = p.map(force_data,
                                                zip(repeat(boot_size), result["analysis"]),
                                                chunksize=1)

                        for metric_name, metric_name_long, data_process, analysis in results_precalc:
                            if first_budget_line and not header_just_printed:
                                if screen_width % 2 == 1:
                                    print("-" + " -" * (screen_width // 2))
                                else:
                                    print(" -" * (screen_width // 2))
                            first_budget_line = False

                            columns = []
                            for i, (head, width, var) in enumerate(fields):
                                columns.append(var.format(*width, **locals()))

                            # the data
                            print("", " :: ".join(columns), ":: ", flush=True)
                            header_just_printed = False

                            if analysis["goodbench"] != "✓":
                                lower_process = analysis["lower"]
                                upper_process = analysis["upper"]
                                low_out_fence_process = analysis["low_out_fence"]
                                upp_out_fence_process = analysis["upp_out_fence"]
                                stdev_process = analysis["stdev"]
                                mean_process = analysis["mean"]

                                outliers = len([x
                                                for x
                                                in data_process
                                                if lower_process <= x <= upper_process])
                                print(
                                    "{err_prefix}:: Suspicious result analysis:\n"
                                    "{err_prefix}::             {0:>2} / {1:2} ({4:7.3f}%) out of [ {2:>18.13} ; {3:<18.13} ]\n"
                                    "{err_prefix}::                                                            Δ {7:<18.13}\n"
                                    "{err_prefix}::                               Bounds: [ {5:>18.13} ; {6:<18.13} ]\n"
                                    "{err_prefix}::                                                            Δ {8:<18.13}".format(
                                        outliers,
                                        len(data_process),
                                        lower_process,
                                        upper_process,
                                        100.0 * outliers / len(data_process),
                                        min(data_process),
                                        max(data_process),
                                        upper_process - lower_process,
                                        max(data_process) - min(data_process),
                                        err_prefix=err_prefix)
                                )
                                print("{err_prefix}:: Values".format(err_prefix=err_prefix))

                                def aux(x):
                                    try:
                                        return abs(x - mean_process) * 100.0 / stdev_process
                                    except ZeroDivisionError:
                                        return float("inf")

                                print(''.join(
                                    "{err_prefix}:: {0:>30.20}  = avg {1:<+30} = avg {3:+8.3f}% ⨉ σ | {2:17} {4:17} {5:17}\n".format(
                                        x,
                                        x - mean_process,
                                        (lower_process <= x <= upper_process) and "(out of mean±3σ)" or "",
                                        aux(x),
                                        ((low_out_fence_process <= x < analysis["low_inn_fence"]) or (
                                            analysis[
                                                "upp_inn_fence"] <= x < upp_out_fence_process)) and " (mild outlier)" or "",
                                        ((x < low_out_fence_process) or (
                                            upp_out_fence_process < x)) and "(EXTREME outlier)" or "",
                                        err_prefix=err_prefix
                                    )
                                    for x in data_process),
                                    end=''
                                )
                                if abs(analysis["mean_nooutliers_diff"]) > 10.:
                                    badbench.append([problem_name, algo_name, result["budget"], metric_name_long])
                                    print(err_prefix + "::", "#"*22, "#"*67, "#"*22)
                                    print(err_prefix + "::", "#"*22,
                                          "Mean of results changed a lot (> 10%), so probably UNTRUSTED result",
                                          "#"*22)
                                    print(err_prefix + "::", "#"*22, "#"*67, "#"*22)
                                else:
                                    print(err_prefix + "::",
                                          "Mean of results changed a little (< 10%), so probably that's all okay")

    if badbench:
        print("#" * 237)
        for i in badbench:
            print(">>> " + " :: ".join(str(x) for x in i))
