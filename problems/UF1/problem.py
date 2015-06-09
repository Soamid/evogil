import math

n = 30
p_no = 150
emoa_points = [i / (p_no - 1) for i in range(p_no)]

pareto_front = [(f1, 1 - math.sqrt(f1)) for f1 in emoa_points]
pareto_set = []

J1 = [j for j in range(2, n+1) if j % 2]
J2 = [j for j in range(2, n+1) if not j % 2]


def base_fit(x, J):
    return 2 / len(J) * sum((x[j-1] - math.sin(6 * math.pi * x[0] + j * math.pi / n)) ** 2
                                    for j in J)

def fit_1(x):
    return x[0] + base_fit(x, J1)


def fit_2(x):
    return 1 - math.sqrt(x[0]) + base_fit(x, J2)


name = 'UF1'
fitnesses = [fit_1, fit_2]
dims = [(0, 1)] + [(-1, 1)] * (n - 1)