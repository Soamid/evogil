import math

n = 10
eps = 0.1

pareto_front = [[i / (2 * n), 1 - i / (2 * n)] for i in range(2 * n + 1)]
pareto_set = []

J1 = [j for j in range(2, n + 1) if j % 2]
J2 = [j for j in range(2, n + 1) if not j % 2]


def yj(x, j):
    return x[j - 1] - math.sin(6 * math.pi * x[0] + (j * math.pi) / n)


def h(t):
    return 2 * t ** 2 - math.cos(4 * math.pi * t) + 1


def base_fit(x, J):
    return (1 / (2 * n) + eps) * math.fabs(math.sin(2 * n * math.pi * x[0])) + (2 * sum(h(yj(x, j)) for j in J)) / len(
        J)


def fit_1(x):
    return x[0] + base_fit(x, J1)


def fit_2(x):
    return 1 - x[0] + base_fit(x, J2)


name = 'UF5'
fitnesses = [fit_1, fit_2]
dims = [(0, 1)] + [(-1, 1)] * (n - 1)