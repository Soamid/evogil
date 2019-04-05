# base
from contextlib import contextmanager, suppress

# numpy + matplotlib
import collections
import matplotlib.pyplot as plt
import sys
from numpy.linalg import LinAlgError

# self
from plots.pictures import algos, algos_order, PLOTS_DIR
from statistic.ranking import best_func
from simulation.serialization import RunResult, RESULTS_DIR
from statistic.stats_bootstrap import find_acceptable_result_for_budget


@contextmanager
def plt_figure():
    try:
        yield
    finally:
        plt.close("all")


def prepare_data(data):
    return [[v if v else sys.float_info.epsilon for v in d] for d in data]


def violin(args):
    global_data = collections.defaultdict(dict)

    boot_size = int(args["--bootstrap"])

    for problem_name, problem_mod, algorithms in RunResult.each_result(RESULTS_DIR):
        for algo_name, results in algorithms:
            max_result = find_acceptable_result_for_budget(list(results), boot_size)
            if max_result:
                for metric_name, metric_name_long, data_process in max_result[
                    "analysis"
                ]:
                    if metric_name in best_func:
                        data_process = list(x() for x in data_process)
                        global_data[(problem_name, metric_name)][
                            algo_name
                        ] = data_process

    print(global_data[("UF2", "pdi")])
    print()
    for problem, metric in global_data:
        try:
            algo_data = global_data[(problem, metric)]

            accepted_algos = [
                algo_name
                for algo_name in algos_order
                if algo_name in algo_data
                and algo_data[algo_name] != [0.0] * len(algo_data[algo_name])
            ]

            data = prepare_data([algo_data[algo_name] for algo_name in accepted_algos])
            if metric == "pdi":
                print(data)
            # if problem == 'UF2' and metric == 'pdi':
            #     print(data)
            if data:
                with plt_figure():
                    plt.figure(num=None, facecolor="w", edgecolor="k")
                    # plt.yscale('log')
                    x_index = range(1, len(accepted_algos) + 1)
                    plt.ylabel(metric, fontsize=20)
                    plt.xticks(
                        x_index,
                        [algos[algo_name][0] for algo_name in accepted_algos],
                        rotation=80,
                    )
                    for i in x_index:
                        plt.axvline(i, lw=0.9, c="#AFAFAF", alpha=0.5)
                    plt.tick_params(axis="both", labelsize=15)

                    result = plt.violinplot(
                        data,
                        showmeans=True,
                        showextrema=True,
                        showmedians=True,
                        widths=0.8,
                    )

                    for pc in result["bodies"]:
                        pc.set_facecolor("0.8")
                        # pc.set_sizes([0.8])

                    result["cbars"].set_color("black")
                    result["cmeans"].set_color("black")
                    result["cmins"].set_color("black")
                    result["cmaxes"].set_color("black")
                    result["cmedians"].set_color("black")

                    result["cmeans"].set_linewidths([2])

                    plt.tight_layout()
                    # os.makedirs(PLOTS_DIR, exist_ok=True)
                    # os.makedirs(os.path.join(PLOTS_DIR, 'plots_violin'), exist_ok=True)
                    problem_moea = problem.replace("emoa", "moea")
                    metric_short = metric.replace("distance from Pareto front", "dst")
                    fig_path = (
                        PLOTS_DIR
                        / "plots_violin"
                        / "figures_violin_{}_{}.eps".format(problem_moea, metric_short)
                    )
                    fig_path_pdf = (
                        PLOTS_DIR
                        / "plots_violin"
                        / "figures_violin_{}_{}.pdf".format(problem_moea, metric_short)
                    )
                    with suppress(FileExistsError):
                        fig_path.parent.mkdir(parents=True)
                    print(fig_path)
                    plt.savefig(str(fig_path))
                    plt.savefig(str(fig_path_pdf))
        except KeyError as e:
            print(
                "Missing algo: {}, (problem: {}, metrics: {}".format(e, problem, metric)
            )
        except LinAlgError as e:
            print("Zero vector? : {}, {}: {}".format(problem, metric, e))
