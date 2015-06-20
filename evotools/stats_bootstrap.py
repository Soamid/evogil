import random
from math import sqrt
import numpy



def average(xs):
    if len(xs) == 0:
        return -float("inf")
    return sum(xs) * 1.0 / len(xs)

def sample_wr(population, k):
    """Chooses k random elements (with replacement) from a population"""
    n = len(population) - 1
    return [population[int(random.randint(0, n))] for i in range(k)]


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
    # noinspection PyRedeclaratione
    extr_outliers = len([x
                         for x in data_process
                         if (x < low_out_fence or upp_out_fence < x)])
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
        mean_nooutliers = float("inf")

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
        stdev = lower = upper = mean = float("inf")
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

    return {
        "low_inn_fence": low_inn_fence,
        "upp_inn_fence": upp_inn_fence,
        "low_out_fence": low_out_fence,
        "upp_out_fence": upp_out_fence,
        "stdev": stdev,
        "mean": mean,
        "lower": lower,
        "upper": upper,
        "goodbench": goodbench,
        "btstrpd": btstrpd,
        "mild_outliers": mild_outliers,
        "extr_outliers": extr_outliers,
        "metrics_nooutliers": metrics_nooutliers,
        "mean_nooutliers_diff": mean_nooutliers_diff,
        "stdev_nooutliers": stdev_nooutliers,
        "stdev_nooutliers_diff": stdev_nooutliers_diff,
        "pr_dispersion": pr_dispersion,
        "dispersion_warn": dispersion_warn
    }
    # return low_inn_fence, upp_inn_fence, low_out_fence, upp_out_fence, stdev, mean, lower, upper, goodbench, btstrpd,
    # stdev, mild_outliers, extr_outliers, metrics_nooutliers, mean_nooutliers_diff, stdev_nooutliers,
    # stdev_nooutliers_diff, pr_dispersion, dispersion_warn