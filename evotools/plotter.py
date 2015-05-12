import json
from matplotlib import pyplot as plt
import glob
from collections import defaultdict
from evotools import ea_utils
from evotools.serialization import get_current_time

EXTENT = "extent"
DISTRIBUTION = "distribution"
DISTANCE_FROM_PARETO = "distance_from_pareto"


def plot_quality(series, metrics_name, problem_name):
    f = plt.figure(figsize=(16, 12), dpi=470)
    plt.title("{0} : {1}".format(metrics_name, problem_name))
    plt.xlabel('Cost')
    plt.ylabel('Quality')
    plt.axhline(linestyle='--', lw='0.75', c='#dddddd')
    plt.axvline(linestyle='--', lw='0.75', c='#dddddd')

    for alg in series:
        (costs, values) = series[alg]
        plt.plot(costs, values, linestyle='-', marker='o', label=alg)

    plt.yscale('log')
    path = "_".join(["quality", problem_name, metrics_name, get_current_time()])
    plt.legend(loc=4)
    plt.savefig(path + ".png")
    plt.close(f)


def load_gathered(problem, metrics, algorithm="*", date="*"):
    path = "/".join(["jsoned", problem, algorithm, metrics]) + "_" + date + ".json"

    series = {}

    for filename in glob.glob(path):
        with open(filename, 'rb') as f:
            result = json.load(f)
            print(result)
            alg = result["algorithm"]

            if alg not in series:
                series[alg] = defaultdict(list)

            results = series[alg]

            cost = result["cost"]
            value = result["metrics"]

            results[cost].append(value)

    for alg in series:
        results = series[alg]
        costs = [key for key in sorted(results.keys())]
        values = [sum(results[cost]) / len(results[cost]) for cost in costs]
        series[alg] = (costs, values)

    return series, metrics, problem


if __name__ == "__main__":
    result = load_gathered("ZDT4", DISTANCE_FROM_PARETO)
    plot_quality(*result)

