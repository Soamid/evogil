import functools
import math
import operator

n = 30
p_no = 150
emoa_points = [i / (p_no - 1) for i in range(p_no)]

pareto_front = [[f1, 1 - math.sqrt(f1)] for f1 in emoa_points]
pareto_set = []

J1 = [j for j in range(2, n + 1) if j % 2]
J2 = [j for j in range(2, n + 1) if not j % 2]


def yj(x, j):
    return x[j - 1] - math.pow(x[0], 0.5 * (1.0 + (3 * (j - 2)) / (n - 2)))


def base_fit(x, J):
    Y = [yj(x, j) for j in J]
    return 2*(4 * sum(map(lambda y: y ** 2, Y)) - 2 * functools.reduce(operator.mul,
                                                                    [math.cos((20 * Y[j] * math.pi) / math.sqrt(J[j]))
                                                                     for j in range(len(J))]) + 2) / len(J)


def fit_1(x):
    return x[0] + base_fit(x, J1)


def fit_2(x):
    return 1 - math.sqrt(x[0]) + base_fit(x, J2)


name = 'UF3'
fitnesses = [fit_1, fit_2]
dims = [(0, 1)]*n