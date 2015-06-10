import math
import itertools

n = 30
p_no = 150

xy_series_no = int(math.sqrt(p_no))
x_points = [i / (xy_series_no - 1) for i in range(xy_series_no)]
y_points = [i / (xy_series_no - 1) for i in range(xy_series_no)]

pareto_front = [(x, y, math.pow(-x ** 2 - y ** 2 + 1, 1 / 3)) for x, y in itertools.product(x_points, y_points) if
                x ** 2 + y ** 2 <= 1]
pareto_set = []

J1 = [j for j in range(3, n + 1) if (j - 1) % 3]
J2 = [j for j in range(3, n + 1) if (j - 2) % 3]
J3 = [j for j in range(3, n + 1) if j % 3]


def base_fit(x, J):
    return (2 * sum((x[j - 1] - 2 * x[1] * math.sin(2 * math.pi * x[0] + (j * math.pi) / n)) ** 2 for j in J)) / len(J)


def fit_1(x):
    return math.cos(0.5 * x[0] * math.pi) * math.cos(0.5 * x[1] * math.pi) + base_fit(x, J1)


def fit_2(x):
    return math.cos(0.5 * x[0] * math.pi) * math.sin(0.5 * x[1] * math.pi) + base_fit(x, J2)


def fit_3(x):
    return math.sin(0.5 * x[0] * math.pi) + base_fit(x, J3)


name = 'UF8'
fitnesses = [fit_1, fit_2, fit_3]
dims = [(0, 1)] * 2 + [(-2, 2)] * (n - 2)