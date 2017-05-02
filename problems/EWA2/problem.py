import math

N = 50
M = 30


def f1(x):
    return math.sin(N * x[0]) * math.cos(M * x[1]) + 1


def f2(x):
    return math.sin(M * x[0]) * math.cos(N * x[1]) + 1


name = 'EWA2'
dims = [(0, 1), (0, 1)]
fitnesses = [f1, f2]

pareto_front = [[0.0, 0.0]]
pareto_set = []

