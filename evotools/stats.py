from evotools.serialization import RunResult
from evotools.stats_bootstrap import yield_analysis


def statistics(args, print_stdout=True):
    badbench = []
    cost_badbench = []
    boot_size = int(args['--bootstrap'])

    fields = [
        ("PROBLEM",                     [9],             "{problem_name:{0}}"),
        ("ALGO",                        [14],            "{algo_name:{0}}"),
        ("N",                           [2],             "{len_data:>{0}}"),
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

    def print_header():
        print()
        print('..'.join('[{0:^{1}}]'.format(head, sum(width))
                        for head, width, var
                        in fields)
              + "..",
              flush=True)
        return True

    for problem_name, algorithms in RunResult.each_result():
        for algo_name, budgets in algorithms:
            header_just_printed = print_header()

            for result in budgets:
                len_data = len(result["results"])

                first_budget_line = True

                for metric_name, metric_name_long, data_process in result["analysis"]:
                    if first_budget_line and not header_just_printed:
                        print("-" + " -" * 118)
                    first_budget_line = False

                    analysis = yield_analysis(data_process, boot_size)

                    columns = []
                    for i, (head, width, var) in enumerate(fields):
                        columns.append(var.format(*width, **locals()))

                    # the data
                    print("", " :: ".join(columns), ":: ", flush=True)
                    header_just_printed = False

                    prefix = " " * 72
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
                            "{prefix}:: Suspicious result analysis:\n"
                            "{prefix}::             {0:>2} / {1:2} ({4:7.3f}%) out of [ {2:>18.13} ; {3:<18.13} ]\n"
                            "{prefix}::                                                            Δ {7:<18.13}\n"
                            "{prefix}::                               Bounds: [ {5:>18.13} ; {6:<18.13} ]\n"
                            "{prefix}::                                                            Δ {8:<18.13}".format(
                                outliers,
                                len(data_process),
                                lower_process,
                                upper_process,
                                100.0 * outliers / len(data_process),
                                min(data_process),
                                max(data_process),
                                upper_process - lower_process,
                                max(data_process) - min(data_process),
                                prefix=prefix)
                        )
                        print("{prefix}:: Values".format(prefix=prefix))

                        def aux(x):
                            try:
                                return abs(x - mean_process) * 100.0 / stdev_process
                            except ZeroDivisionError:
                                return float("inf")

                        print(''.join(
                            "{prefix}:: {0:>30.20}  = avg {1:<+30} = avg {3:+8.3f}% ⨉ σ | {2:17} {4:17} {5:17}\n".format(
                                x,
                                x - mean_process,
                                (lower_process <= x <= upper_process) and "(out of mean±3σ)" or "",
                                aux(x),
                                ((low_out_fence_process <= x < analysis["low_inn_fence"]) or (
                                    analysis[
                                        "upp_inn_fence"] <= x < upp_out_fence_process)) and " (mild outlier)" or "",
                                ((x < low_out_fence_process) or (
                                    upp_out_fence_process < x)) and "(EXTREME outlier)" or "",
                                prefix=prefix
                            )
                            for x in data_process),
                            end=''
                        )
                        if abs(analysis["mean_nooutliers_diff"]) > 10.:
                            badbench.append([problem_name, algo_name, result["budget"], metric_name_long])
                            print(prefix + "::", "#"*22, "#"*67, "#"*22)
                            print(prefix + "::", "#"*22,
                                  "Mean of results changed a lot (> 10%), so probably UNTRUSTED result",
                                  "#"*22)
                            print(prefix + "::", "#"*22, "#"*67, "#"*22)
                        else:
                            print(prefix + "::",
                                  "Mean of results changed a little (< 10%), so probably that's all okay")

    if print_stdout and badbench:
        print("#" * 237)
        for i in badbench:
            print(">>> " + " :: ".join(str(x) for x in i))
