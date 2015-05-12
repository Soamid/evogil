# base
import random
import json
from math import sqrt

# numpy
import numpy

# self
from evotools.benchmark_results import iterate_results


def sample_wr(population, k):
    """Chooses k random elements (with replacement) from a population"""
    n = len(population) - 1
    return [population[int(random.randint(0, n))] for i in range(k)]


def average(xs):
    if len(xs) == 0:
        return -float("inf")
    return sum(xs) * 1.0 / len(xs)


def bootstrap(population, f, n, k, alpha):
    btstrp = sorted(f(sample_wr(population, k)) for i in range(n))
    return {
        "confidence": 100.0 * (1 - 2 * alpha),
        "from": btstrp[int(1.0 * n * alpha)],
        "to": btstrp[int(1.0 * n * (1 - alpha))],
        "metrics": f(population)
    }

def yield_analysis(data_process, boot_size):
    q1 = numpy.percentile(data_process, 25)
    q3 = numpy.percentile(data_process, 75)
    iq = q3 - q1
    low_inn_fence = q1 - 1.5*iq
    upp_inn_fence = q3 + 1.5*iq
    low_out_fence = q1 - 3*iq
    upp_out_fence = q3 + 3*iq
    # noinspection PyRedeclaration
    extr_outliers = len([x for x in data_process if (x < low_out_fence or upp_out_fence < x)])
    # noinspection PyRedeclaration
    mild_outliers = len([x for x in data_process if (x < low_inn_fence or upp_inn_fence < x)]) - extr_outliers
    extr_outliers = extr_outliers > 0 and "{0:6.2f}%".format(extr_outliers * 100.0 / len(data_process)) or "--"
    mild_outliers = mild_outliers > 0 and "{0:6.2f}%".format(mild_outliers * 100.0 / len(data_process)) or "--"
    metrics_nooutliers = average([x for x in data_process if low_inn_fence <= x <= upp_inn_fence])
    try:
        mean_nooutliers = float(average([x for x in data_process if low_inn_fence <= x <= upp_inn_fence]))
        variance_nooutliers = [(x - mean_nooutliers) ** 2 for x in data_process if low_inn_fence <= x <= upp_inn_fence]
        stdev_nooutliers = sqrt(average(variance_nooutliers))
    except ValueError:
        stdev_nooutliers = -float("inf")

    btstrpd = bootstrap(data_process, average, boot_size, int(len(data_process) * 0.66), 0.025)

    goodbench = "✓"
    try:
        mean = float(average(data_process))
        variance = [(x - mean) ** 2 for x in data_process]
        stdev = sqrt(average(variance))
        lower = mean - 3 * stdev
        upper = mean + 3 * stdev
        if len([x for x in data_process if lower <= x <= upper]) < 0.95 * len(data_process):
            goodbench = "╳╳╳╳╳"
    except ValueError:
        stdev = float("inf")
        goodbench = "?"

    try:
        mean_nooutliers_diff = 100.0 * (mean_nooutliers - mean) / mean
    except ZeroDivisionError:
        mean_nooutliers_diff = float("inf")

    try:
        stdev_nooutliers_diff = 100.0 * (stdev_nooutliers - stdev) / stdev
    except ZeroDivisionError:
        stdev_nooutliers_diff = float("inf")

    dispersion_warn = ""
    try:
        pr_dispersion = 100.0 * (float(btstrpd["to"]) - float(btstrpd["from"])) / btstrpd["metrics"]
        if abs(pr_dispersion) > 30.:
            dispersion_warn = " HIGH"
    except ZeroDivisionError:
        pr_dispersion = float("+Infinity")

    return low_inn_fence, upp_inn_fence, low_out_fence, upp_out_fence, stdev, mean, lower, upper, goodbench, btstrpd, stdev, mild_outliers, extr_outliers, metrics_nooutliers, mean_nooutliers_diff, stdev_nooutliers, stdev_nooutliers_diff, pr_dispersion, dispersion_warn

def statistics(args, print_stdout=True):
    badbench = []
    cost_badbench = []
    
    for loop in iterate_results():

        d_problem    = loop['d_problem']
        sd_problem   = loop['sd_problem']
        
        d_algorithm  = loop['d_algorithm']
        sd_algorithm = loop['sd_algorithm']
        
        d_testname   = loop['d_testname']
        sd_testname  = loop['sd_testname']
        
        d_budget     = loop['d_budget']
        sd_budget    = loop['sd_budget']

        data         = loop['data']
        cost         = loop['cost']
        len_data = len(data)

        metrics_name_long = loop['metrics_name_long']
        metrics_name      = loop['metrics_name']


        low_inn_fence, upp_inn_fence, low_out_fence, upp_out_fence, stdev, mean, lower, upper, goodbench, btstrpd, stdev, mild_outliers, extr_outliers, metrics_nooutliers, mean_nooutliers_diff, stdev_nooutliers, stdev_nooutliers_diff, pr_dispersion, dispersion_warn = yield_analysis(data, int(args['--bootstrap']))
        cost_low_inn_fence, cost_upp_inn_fence, cost_low_out_fence, cost_upp_out_fence, cost_stdev, cost_mean, cost_lower, cost_upper, cost_goodbench, cost_btstrpd, cost_stdev, cost_mild_outliers, cost_extr_outliers, cost_metrics_nooutliers, cost_mean_nooutliers_diff, cost_stdev_nooutliers, cost_stdev_nooutliers_diff, cost_pr_dispersion, cost_dispersion_warn = yield_analysis(cost, int(args['--bootstrap']))

        probname = str(d_problem.name)
        if print_stdout and not sd_problem:
            print("=" * 436)


        algoname = not sd_algorithm and str(d_algorithm.name) or ""

        test_name = not sd_testname and str(d_testname.name)[5:] or ""
        fields = [
            ("PROBLEM"                    , [9],          "{probname:{0}}"                                                                                   ),
            ("ALGO"                       , [10],         "{algoname:{0}}"                                                                                   ),
            ("TEST"                       , [24],         "{test_name:{0}}"                                                                                  ),
            ("N"                          , [2],          "{len_data:>{0}}"                                                                                   ),
            ("Budgt"                      , [5],          "{budg_cost!s:>{0}}"                                                                               ),
            ("METRICS OY"                 , [15],         "{metrics_name:^{0}}"                                                                              ),
            ("✓"                          , [5],          "{goodbench:^{0}}"                                                                                 ),
            ("RESULT, confidence interval", [10,10,10,6], "{btstrpd[from]: >0{0}.3f} ≤ {btstrpd[metrics]: >{1}.3f} ≤ {btstrpd[to]: >0{2}.3f}"                ),
            ("σ"                          , [10],         "{stdev: >{0}.3f}"                                                                                 ),
            ("OUTLIERS"                   , [7,7,12],     "{mild_outliers:>{0}} mild {extr_outliers:>{1}} extr."                                             ),
            ("RES w/o outliers"           , [10,10,4],    "{metrics_nooutliers:>{0}.3f} ({mean_nooutliers_diff:>+{1}.3f}%)"                                  ),
            ("σ w/o outliers"             , [10,10,4],    "{stdev_nooutliers:>{0}.3f} ({stdev_nooutliers_diff:>{1}.3f}%)"                                    ),
            ("(C INT)/METRICS"            , [7,10,2],     "{pr_dispersion: >{0}.3f}% {dispersion_warn:<{1}}"                                                 ),
            ("OX"                         , [5],          "cost "                                                                                            ),
            ("✓"                          , [5],          "{cost_goodbench:^{0}}"                                                                            ),
            ("RESULT, confidence interval", [10,10,10,6], "{cost_btstrpd[from]: >0{0}.3f} ≤ {cost_btstrpd[metrics]: >{1}.3f} ≤ {cost_btstrpd[to]: >0{2}.3f}" ),
            ("σ"                          , [10],         "{cost_stdev: <{0}.3f}"                                                                            ),
            ("OUTLIERS"                   , [7,7,12],     "{cost_mild_outliers:>{0}} mild {cost_extr_outliers:>{1}} extr."                                   ),
            ("RES w/o outliers"           , [10,10,4],    "{cost_metrics_nooutliers:>{0}.3f} ({cost_mean_nooutliers_diff:>+{1}.3f}%)"                        ),
            ("σ w/o outliers"             , [10,10,4],    "{cost_stdev_nooutliers:>{0}.3f} ({cost_stdev_nooutliers_diff:>{1}.3f}%)"                          ),
            ("(C INT)/METRICS"            , [7,10,2],     "{cost_pr_dispersion: >{0}.3f}% {cost_dispersion_warn:<{1}}"                                       )
        ]
        if print_stdout and not sd_testname:
            print('..'.join('[{0:^{1}}]'.format(head,sum(width)) for (i, (head,width,var)) in enumerate(fields)) + "..", flush=True)

        budg_cost = not sd_budget and str(d_budget.name) or ""

        lcls = locals()
        if print_stdout:
            print(" " + " :: ".join(var.format(*width, **lcls) for (i, (head,width,var)) in enumerate(fields)) + " :: ", flush=True)

        def stdout_abstract_analysis(mean_nooutliers_diff_process, goodbench_process, lower_process, upper_process, data_process, low_inn_fence_process, upp_inn_fence_process, low_out_fence_process, upp_out_fence_process, stdev_process, mean_process, badbench_process, prefix):
            prefix = " " * prefix
            if goodbench_process != "✓":
                outliers = len([x for x in data_process if lower_process <= x <= upper_process])
                print(
                    "{prefix}:: Suspicious result analysis:\n"
                    "{prefix}::             {0:>2} / {1:2} ({4:7.3f}%) out of [ {2:>18.13} ; {3:<18.13} ]\n"
                    "{prefix}::                                                            Δ {7:<18.13}\n"
                    "{prefix}::                               Bounds: [ {5:>18.13} ; {6:<18.13} ]\n"
                    "{prefix}::                                                            Δ {8:<18.13}".format(
                        outliers, len(data_process), lower_process, upper_process, 100.0 * outliers / len(data_process), min(data_process), max(data_process), upper_process - lower_process, max(data_process)-min(data_process),prefix=prefix)
                )
                print(
                    "{prefix}:: Values".format(prefix=prefix))
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
                        ((low_out_fence_process <= x < low_inn_fence_process) or (upp_inn_fence_process <= x < upp_out_fence_process)) and " (mild outlier)" or "",
                        ((x < low_out_fence_process) or (upp_out_fence_process < x)) and "(EXTREME outlier)" or "",
                        prefix=prefix
                    )
                    for x in data_process),
                    end=''
                )
                if abs(mean_nooutliers_diff_process) > 10.:
                    badbench_process.append(d_budget)
                    print("{prefix}:: #################### ################################################################### ####################".format(prefix=prefix))
                    print("{prefix}:: #################### Mean of results changed a lot (> 10%), so probably UNTRUSTED result ####################".format(prefix=prefix))
                    print("{prefix}:: #################### ################################################################### ####################".format(prefix=prefix))
                else:
                    print("{prefix}:: Mean of results changed a little (< 10%), so probably that's all okay".format(prefix=prefix))
        if print_stdout:
            stdout_abstract_analysis(mean_nooutliers_diff, goodbench, lower, upper, data, low_inn_fence, upp_inn_fence, low_out_fence, upp_out_fence, stdev, mean, badbench, prefix=62)
            stdout_abstract_analysis(cost_mean_nooutliers_diff, cost_goodbench, cost_lower, cost_upper, [float(x) for x in cost], cost_low_inn_fence, cost_upp_inn_fence, cost_low_out_fence, cost_upp_out_fence, cost_stdev, cost_mean, cost_badbench, prefix=253)

    if print_stdout and (badbench or cost_badbench):
        print("#" * 436)
        for i in badbench:
            print(">>> " + str(i))
