import functools
import math

dims = [(-5, 5), (-5, 5), (-5, 5)]
pareto_set = []

p_no = 150
emoa_points = [i/(p_no-1) for i in range(p_no)]

p_no2 = 300
emoa_points2 = [i/(p_no2-1) for i in range(p_no2)]


def emoa_fitness_2(f1, g, h, x):
    y = g(x[1:])
    return y * h(f1(x[0]), y)


def subfit1(x, f1):
    return f1(x[0])


def subfit2(x, f1, g, h):
    return emoa_fitness_2(f1, g, h, x)


def emoa_fitnesses(f1, g, h, dimensions, letter, known_front):
    return ([functools.partial(subfit1, f1=f1),
             functools.partial(subfit2, f1=f1, g=g, h=h)],
            [(0, 1) for _ in range(dimensions)],
            "coemoa_" + letter,
            known_front)


def emoa_fitnesses2(f1, g, h, dimensions, letter, known_front):
    return ([subfit1,
             functools.partial(subfit2, f1=f1, g=g, h=h)],
            [(0, 1)] + [(-5, 5) for _ in range(dimensions-1)],
            "coemoa_" + letter,
            known_front)


spi = 6 * math.pi


def f1e(x):
    return 1 - math.exp(-4 * x) * (math.sin(spi * x) ** 6)


def ge(xs):
    return 1 + 5.19615 * sum(xs) ** 0.25


def he(f1, g):
    return 1 - (f1 / g) ** 2

emoa_e_analytical = [[f1e(x) for x in emoa_points], [1-f1e(x)*f1e(x) for x in emoa_points]]
fitnesses, dims, name, pareto_front = emoa_fitnesses(f1e, ge, he, 10, 'e', emoa_e_analytical)
pareto_front = [[x, y] for x, y in zip(pareto_front[0], pareto_front[1])]