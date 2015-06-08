import math

n = 30
p_no = 150
emoa_points = [i / (p_no - 1) for i in range(p_no)]

pareto_front = [(f1, 1 - math.sqrt(f1)) for f1 in emoa_points]
pareto_set = []

J1 = [j for j in range(1, n) if j % 2]
J2 = [j for j in range(1, n) if not j % 2]


def base_fit(x, J, trig):
    return 2/len(J) * sum((x[j] - (0.3 * x[0] ** 2 * math.cos(24 * math.pi * x[0] + 4 * j * math.pi / n) + 0.6 * x[0]) * trig(
        6 * math.pi * x[0] + j * math.pi / n))**2 for j in J)


def fit_1(x):
    return x[0] + base_fit(x, J1, math.cos)


def fit_2(x):
    return 1 - math.sqrt(x[0]) + base_fit(x, J2, math.sin)


name = 'UF2'
fitnesses = [fit_1, fit_2]
dims = [(0, 1)] + [(-1, 1)] * (n - 1)