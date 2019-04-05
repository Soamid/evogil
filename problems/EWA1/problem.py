import math

N = 50


def f1(x):
    return math.sin(N * x[0]) * math.cos(N * x[1]) + 1


def f2(x):
    return ((x[0] - 0.5) ** 2) * ((x[1] - 0.5) ** 2)


name = "EWA1"
dims = [(0, 1), (0, 1)]
fitnesses = [f1, f2]

pareto_front = [[0.0, 0.0]]
pareto_set = []
