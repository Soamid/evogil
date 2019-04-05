import math
import numpy
import random
from evotools.ea_utils import paretofront_layers

EPSILON = numpy.finfo(float).eps


# polynomial mutation
def mutate(xs, dims, mutation_rate, eta):
    new_xs = [x for x in xs]
    for i, dim in enumerate(dims):
        if random.random() > mutation_rate:
            continue

        y = xs[i]
        lb, ub = dim

        delta1 = (y - lb) / (ub - lb + EPSILON)
        delta2 = (ub - y) / (ub - lb + EPSILON)

        mut_pow = 1.0 / (eta + 1.0)

        rnd = random.random()

        if rnd <= 0.5:
            xy = 1.0 - delta1
            try:
                val = 2.0 * rnd + (1.0 - 2.0 * rnd) * (pow(xy, (eta + 1.0)))
            except FloatingPointError:
                val = 2.0 * rnd
            delta_q = pow(val, mut_pow) - 1.0
        else:
            xy = 1.0 - delta2
            try:
                val = 2.0 * (1.0 - rnd) + 2.0 * (rnd - 0.5) * (pow(xy, (eta + 1.0)))
            except FloatingPointError:
                val = 2.0 * rnd
            delta_q = 1.0 - (pow(val, mut_pow))

        y += delta_q * (ub - lb)
        y = min(ub, max(lb, y))

        new_xs[i] = y
    return new_xs


def old_mutate(xs, dimensions, mutation_probability, mutation_variance):
    def coin():
        return random.random() < mutation_probability

    return [
        min(max(a, (random.gauss(x, sigma))), b) if coin() else x
        for x, (a, b), sigma in zip(xs, dimensions, mutation_variance)
    ]


# simulated binary crossover
def crossover(xs, ys, dims, crossover_rate, eta):
    new_xs = [x for x in xs]
    new_ys = [y for y in ys]

    if random.random() > crossover_rate:
        return random.choice([new_xs, new_ys])

    for i, dim in enumerate(dims):
        if random.random() > 0.5:
            continue
        if math.fabs(xs[i] - ys[i]) <= EPSILON:
            continue

        y1 = min(xs[i], ys[i])
        y2 = max(xs[i], ys[i])

        lb, ub = dim

        rand = random.random()

        # child a
        beta = 1.0 + (2.0 * (y1 - lb) / (y2 - y1 + EPSILON))
        try:
            alpha = 2.0 - pow(beta, -(eta + 1.0))
        except FloatingPointError:
            alpha = 2.0
        beta_q = get_beta_q(rand, alpha, eta)

        new_xs[i] = 0.5 * ((y1 + y2) - beta_q * (y2 - y1))

        # child b
        beta = 1.0 + (2.0 * (ub - y2) / (y2 - y1 + EPSILON))
        try:
            alpha = 2.0 - pow(beta, -(eta + 1.0))
        except FloatingPointError:
            alpha = 2.0
        beta_q = get_beta_q(rand, alpha, eta)

        new_ys[i] = 0.5 * ((y1 + y2) + beta_q * (y2 - y1))

        # boundary checking
        new_xs[i] = min(ub, max(lb, new_xs[i]))
        new_ys[i] = min(ub, max(lb, new_ys[i]))

        if random.random() > 0.5:
            temp = new_xs[i]
            new_xs[i] = new_ys[i]
            new_ys[i] = temp

    return random.choice([new_xs, new_ys])


def get_beta_q(rand, alpha, eta):
    if rand <= (1.0 / alpha):
        beta_q = pow((rand * alpha), (1.0 / (eta + 1.0)))
    else:
        beta_q = pow((1.0 / (2.0 - rand * alpha)), (1.0 / (eta + 1.0)))
    return beta_q


def old_crossover(xs, ys):
    return [random.uniform(x, y) for x, y in zip(xs, ys)]


def crossover_triangular(xs, ys):
    return [random.triangular(low=min(x, y), high=max(x, y)) for x, y in zip(xs, ys)]


def crossover_beta(xs, ys, dimensions, crossover_variance):
    """ Rozkład beta - https://en.wikipedia.org/wiki/File:Beta_distribution_pdf.svg .
    Wyznacza a na podstawie zadanej wariancji.
    :warning: Wariancja v musi spełniać: v/(b-a) <= 0.25 gdzie [a,b] jest przestrzenią.
    """
    return [
        random.betavariate(v / (b - a), v / (b - a)) * abs(x - y) + min(x, y)
        for x, y, (a, b), v in zip(xs, ys, dimensions, crossover_variance)
    ]


def average_indiv(population):
    """ :return: Zwraca 'średniego' osobnika. """
    res = numpy.average(population, axis=0)
    if type(res) == numpy.float64:
        return []
    return list(res)


def rank(individuals: "Iterator Individual", calc_objective):
    """
    :param individuals: Grupa indywiduów.
    :param calc_objective: Określa jak otrzymać wektor wyników.
    :return: Itertator: posortowane dane wejściowe od najlepszych do najgorszych.
    """
    return iter(
        indiv
        for eqv_class in paretofront_layers(individuals, fitfun_res=calc_objective)
        for indiv in eqv_class
    )


def get_indivs_inorder(self, fitnesses, population):
    """ :return: Iterator: bieżąca populacja posortowana od najlepszych do najgorszych. """

    def calc_objective(ind):
        return [f(ind) for f in fitnesses]

    return rank(population, calc_objective)
