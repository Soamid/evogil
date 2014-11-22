# https://en.wikipedia.org/wiki/Test_functions_for_optimization
from math import cos, exp, sqrt, e, pi


def fit(x):
    pi2 = 2.*pi
    return (-20 * exp(-0.2 * sqrt(0.5 * (x[0]**2 + x[1]**2)))
            - exp(0.5 * (cos(pi2*x[0])+cos(pi2*x[1])))
            + 20 + e)


name = 'ackley'
pareto_front = [(0, 0)]
pareto_set = [(0, 0)]
fitnesses = [fit, fit]
dims = [(-1.5, 1.5), (-1.5, 1.5)]
