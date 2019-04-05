import functools
import math
import operator
import numpy

n = 30
eps = 0.1
p_step = (1 - 1 / (2 * n)) / 150

emoa_points = [
    x
    for i in range(1, n + 1)
    for x in numpy.arange((2 * i - 1) / (2 * n), (2 * i) / (2 * n) + p_step, p_step)
]
pareto_front = [[0, 1]] + [[x, 1 - x] for x in emoa_points]
pareto_set = []

J1 = [j for j in range(2, n + 1) if j % 2]
J2 = [j for j in range(2, n + 1) if not j % 2]


def yj(x, j):
    return x[j - 1] - math.sin(6 * math.pi * x[0] + (j * math.pi) / n)


def inner_base_fit(x, J):
    Y = [yj(x, j) for j in J]
    return (
        2
        * (
            4 * sum(map(lambda y: y ** 2, Y))
            - 2
            * functools.reduce(
                operator.mul,
                [
                    math.cos((20 * Y[j] * math.pi) / math.sqrt(J[j]))
                    for j in range(len(J))
                ],
            )
            + 2
        )
        / len(J)
    )


def base_fit(x, J):
    return max(
        0, 2 * (1 / (2 * n) + eps) * math.sin(2 * n * math.pi * x[0])
    ) + inner_base_fit(x, J)


def fit_1(x):
    return x[0] + base_fit(x, J1)


def fit_2(x):
    return 1 - x[0] + base_fit(x, J2)


name = "UF6"
fitnesses = [fit_1, fit_2]
dims = [(0, 1)] + [(-1, 1)] * (n - 1)
