import functools
import math
import operator
import pathlib

import numpy as np


f_dims = 5

base_dat = pathlib.Path('.') / 'problems' / 'UF12'
bound_30_dat = base_dat / 'R2_DTLZ3_bound_30D.dat'
lambda_30_dat = base_dat / 'R2_DTLZ3_lamda_30D.dat'
m_30_dat = base_dat / 'R2_DTLZ3_M_30D.dat'
m5_dat = base_dat / 'R3_DTLZ3_M5.dat'

with bound_30_dat.open('r') as f:
    bounds_lines = f.readlines()

with lambda_30_dat.open('r') as f:
    lambda_lines = f.readlines()

with m_30_dat.open('r') as f:
    M_lines = f.readlines()

with m5_dat.open('r') as f:
    pf_lines = f.readlines()

lambdas = [float(x) for x in lambda_lines[0].split()]
M = np.array([[float(x) for x in line.split()] for line in M_lines])

pareto_front = [tuple(float(x) for x in line.split()) for line in pf_lines]
pareto_set = []

name = 'UF12'


def z(x):
    return np.dot(M, x)


def z_bis(z):
    return [- lambdas[i] * z[i] if z[i] < 0 else lambdas[i] * z[i] if z[i] > 1 else z[i] for i in range(len(z))]


def psum(z, m):
    return math.sqrt(sum(p(z[i]) ** 2 for i in range(m)))


def S(z, m):
    return 2 / (1 + math.exp(-psum(z, m)))


def p(z_i):
    return -z_i if z_i < 0 else z_i - 1 if z_i > 1 else 0


def g(z):
    return 100 * (len(z) + sum((zi - 0.5) ** 2 - math.cos(20 * math.pi * (zi - 0.5)) for zi in z))


def base_fit_cos(z_bis, m):
    return functools.reduce(operator.mul,
                            [math.cos((z_bis[i] * math.pi) / 2.0) for i in range(m)]) if m > 1 else math.cos(
        (z_bis[0] * math.pi) / 2.0) if m == 1 else 1


def base_fit_up(z, z_b, m):
    return (1 + g(z)) * base_fit_cos(z_b, m - 1) * (math.sin(z_b[m - 1]) if m < f_dims else 1) + 1


def base_fit_bottom(z, z_b, m):
    return S(z_b, m - 1) * base_fit_up(z, z_b, m)


def all_non_negative(z):
    for zi in z:
        if zi < 0:
            return False
    return True


def base_fit(x, m):
    Z = z(x)
    z_b = z_bis(Z)
    return base_fit_up(Z, z_b, m) if all_non_negative(Z) else base_fit_bottom(Z, z_b, m)


def gen_fit(m):
    return lambda x: base_fit(x, m)


fitnesses = [gen_fit(m) for m in range(1, f_dims + 1)]

dims = [(xmin, xmax) for xmin, xmax in zip(*([[float(x) for x in line.split()]
                                              for line in bounds_lines]))]

if __name__ == '__main__':
    print('Dims:')
    print(dims)

    print('Lambdas:')
    print(lambdas)

    print('M:')
    for i in range(len(M)):
        print(" ".join(str(M[i])))

    print('Pareto front:')
    print(pareto_front)

    print(fitnesses)
    print(fitnesses[0]([(xmax - xmin) / 2 for (xmin, xmax) in dims]))

