import functools
import math

p_no = 150
emoa_points = [i / (p_no - 1) for i in range(p_no)]

p_no2 = 300
emoa_points2 = [i / (p_no2 - 1) for i in range(p_no2)]


def emoa_fitness_2(f1, g, h, x):
    y = g(x[1:])
    return y * h(f1(x[0]), y)


def subfit1(x, f1):
    return f1(x[0])


def subfit2(x, f1, g, h):
    return emoa_fitness_2(f1, g, h, x)


def emoa_fitnesses(f1, g, h, dimensions, letter, known_front):
    return (
        [
            functools.partial(subfit1, f1=f1),
            functools.partial(subfit2, f1=f1, g=g, h=h),
        ],
        [(0, 1) for _ in range(dimensions)],
        "ZDT1",
        known_front,
    )


def emoa_fitnesses2(f1, g, h, dimensions, letter, known_front):
    return (
        [subfit1, functools.partial(subfit2, f1=f1, g=g, h=h)],
        [(0, 1)] + [(-5, 5) for _ in range(dimensions - 1)],
        "ZDT1",
        known_front,
    )


def f1a(x):
    return x


def ga(xs):
    return 1 + 0.3103448275862069 * sum(xs)  # 9 / (30-1) = 0.31...


def ha(f1, g):
    return 1 - math.sqrt(abs(f1 / g))


emoa_a_analytical = [[x for x in emoa_points], [1 - math.sqrt(x) for x in emoa_points]]

pareto_set = []
fitnesses, dims, name, pareto_front = emoa_fitnesses(
    f1a, ga, ha, 30, "a", emoa_a_analytical
)

pareto_front = [[x, y] for x, y in zip(pareto_front[0], pareto_front[1])]
