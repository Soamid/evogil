import functools
import math
import operator

n = 30
p_no = 150
emoa_points = [i / (p_no - 1) for i in range(p_no)]

pareto_front = [(f1, 1 - f1 ** 2) for f1 in emoa_points]
pareto_set = []

J1 = [j for j in range(2, n + 1) if j % 2]
J2 = [j for j in range(2, n + 1) if not j % 2]


def yj(x, j):
    return x[j - 1] - math.sin(6 * math.pi * x[0] + (j * math.pi) / n)


def h(t):
    return math.fabs(t) / (1 + math.exp(2 * math.fabs(t)))


def base_fit(x, J):
    return (2 * sum(h(yj(x, j)) for j in J)) / len(J)


def fit_1(x):
    return x[0] + base_fit(x, J1)


def fit_2(x):
    return 1 - x[0]**2 + base_fit(x, J2)


name = 'UF4'
fitnesses = [fit_1, fit_2]
dims = [(0, 1)] + [(-2, 2)] * (n - 1)