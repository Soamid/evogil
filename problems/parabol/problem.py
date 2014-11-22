def fit_a(xs):
    return (xs[0]-3)**2


def fit_b(xs):
    return (xs[1]+2)**2

name = 'parabol'
fitnesses = [fit_a, fit_b]
dims = [(-10, 10), (-10, 10)]
pareto_front = [[0,0]]
pareto_set = [[3, -2]]
