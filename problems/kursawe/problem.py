import math
import pathlib


kursawe_dat = pathlib.Path('.') / 'problems' / 'kursawe' / 'kursawe.dat'

with kursawe_dat.open('r') as f:
    lines = f.readlines()

pareto_front = [[float(x) for x in line.split()]
                for line in lines]
pareto_set = []


def fit_a(xs):
    return sum(-10. * math.exp(-0.2 * math.sqrt(x ** 2 + xn ** 2))
               for x, xn in zip(xs, xs[1:]))


def fit_b(xs):
    return sum(abs(x) ** 0.8 + 5. * math.sin(x ** 3)
               for x in xs)


name = 'kursawe'
fitnesses = [fit_a, fit_b]
dims = [(-5, 5), (-5, 5), (-5, 5)]
