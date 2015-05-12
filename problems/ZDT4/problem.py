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
            "ZDT4",
            known_front)


def emoa_fitnesses2(f1, g, h, dimensions, letter, known_front):
    return ([functools.partial(subfit1, f1=f1),
             functools.partial(subfit2, f1=f1, g=g, h=h)],
            [(0, 1)] + [(-5, 5) for _ in range(dimensions-1)],
            "ZDT4",
            known_front)

fpi = 4 * math.pi


def f1d(x):
    return x


def gd(xs):
    return 91 + sum(x ** 2 - 10 * math.cos(fpi * x) for x in xs)


def hd(f1, g):
    return 1 - math.sqrt(abs(f1 / g))


emoa_d_analytical = [[x
                      for x in emoa_points],
                     [1-math.sqrt(x)
                      for x in emoa_points]]
fitnesses, dims, name, pareto_front = emoa_fitnesses2(f1d, gd, hd, 10, 'd', emoa_d_analytical)
pareto_front = [[x, y] for x, y in zip(pareto_front[0], pareto_front[1])]
