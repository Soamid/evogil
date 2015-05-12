import functools
import math

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
            "ZDT3",
            known_front)


def emoa_fitnesses2(f1, g, h, dimensions, letter, known_front):
    return ([subfit1,
             functools.partial(subfit2, f1=f1, g=g, h=h)],
            [(0, 1)] + [(-5, 5) for _ in range(dimensions-1)],
            "ZDT3",
            known_front)


def f1c(x):
    return x


def gc(xs):
    return 1 + 0.3103448275862069 * sum(xs)  # 9 / (30-1) = 0.31...


def hc(f1, g):
    f1_g = f1 / g
    return 1 - math.sqrt(abs(f1_g)) - f1_g * math.sin(10 * math.pi * f1)


pareto_set = []

c_pre = [[x for x in emoa_points2],
         [1-math.sqrt(x)-x*math.sin(10*math.pi*x)
          for x in emoa_points2]]
to_remove = [False] + [c_pre[1][i] >= c_pre[1][i-1]
                       for i in range(1, len(c_pre[1]))]
emoa_c_analytical = [[c_pre[0][i]
                      for i in range(len(c_pre[1]))
                      if not to_remove[i]],
                     [c_pre[1][i]
                      for i in range(len(c_pre[1]))
                      if not to_remove[i]]]
fitnesses, dims, name, pareto_front = emoa_fitnesses(f1c, gc, hc, 30, 'c', emoa_c_analytical)

pareto_front = [[x, y] for x, y in zip(pareto_front[0], pareto_front[1])]
