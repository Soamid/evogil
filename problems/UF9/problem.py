import math
import itertools

n = 30
eps = 0.1
p_no = 150

xy_series_no = int(math.sqrt(p_no))
x_points = [i / (xy_series_no - 1) for i in range(xy_series_no)]
z_points = [i / (xy_series_no - 1) for i in range(xy_series_no)]

pareto_front = [
    [x, 1 - x - z, z]
    for x, z in itertools.product(x_points, z_points)
    if x <= 0.25 * (1 - z) or x >= 0.75 * (1 - z)
]

J1 = [j for j in range(3, n + 1) if (j - 1) % 3]
J2 = [j for j in range(3, n + 1) if (j - 2) % 3]
J3 = [j for j in range(3, n + 1) if j % 3]


def base_fit(x, J):
    return (
        2
        * sum(
            (x[j - 1] - 2 * x[1] * math.sin(2 * math.pi * x[0] + (j * math.pi) / n))
            ** 2
            for j in J
        )
    ) / len(J)


def fit_1(x):
    return 0.5 * (max(0, (1 + eps) * (1 - 4 * (2 * x[0] - 1) ** 2)) + 2 * x[0]) * x[
        1
    ] + base_fit(x, J1)


def fit_2(x):
    return 0.5 * (max(0, (1 + eps) * (1 - 4 * (2 * x[0] - 1) ** 2)) - 2 * x[0] + 2) * x[
        1
    ] + base_fit(x, J2)


def fit_3(x):
    return 1 - x[1] + base_fit(x, J3)


name = "UF9"
fitnesses = [fit_1, fit_2, fit_3]
dims = [(0, 1)] * 2 + [(-2, 2)] * (n - 2)
