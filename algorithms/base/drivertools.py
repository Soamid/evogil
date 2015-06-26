import numpy
import random
from evotools.ea_utils import paretofront_layers


def old_mutate(xs, dimensions, mutation_probability, mutation_variance):
    def coin():
        return random.random() < mutation_probability

    return [min(max(a, (random.gauss(x, sigma))), b) if coin() else x
            for x, (a, b), sigma in zip(xs, dimensions, mutation_variance)]


from algorithms.NSGAIII.NSGAIII import simulated_binary_crossover, polynomial_mutation, Individual


def mutate(xs, dimensions, rate, eta):
    ind = Individual([x for x in xs])
    polynomial_mutation(ind, dimensions, rate, eta)
    return ind.v


def crossover(xs, ys, dimensions, rate, eta):
    ind_a = Individual([x for x in xs])
    ind_b = Individual([y for y in ys])
    c_a, c_b = simulated_binary_crossover(ind_a, ind_b, dimensions, rate, eta)
    return c_a.v


def old_crossover(xs, ys):
    return [random.uniform(x, y)
            for x, y
            in zip(xs, ys)
    ]


def old_crossover_triangular(xs, ys):
    return [random.triangular(low=min(x, y),
                              high=max(x, y))
            for x, y
            in zip(xs, ys)
    ]


def old_crossover_beta(xs, ys, dimensions, crossover_variance):
    """ Rozkład beta - https://en.wikipedia.org/wiki/File:Beta_distribution_pdf.svg .
    Wyznacza a na podstawie zadanej wariancji.
    :warning: Wariancja v musi spełniać: v/(b-a) <= 0.25 gdzie [a,b] jest przestrzenią.
    """
    return [random.betavariate(v / (b - a), v / (b - a)) * abs(x - y) + min(x, y)
            for x, y, (a, b), v
            in zip(xs, ys, dimensions, crossover_variance)
    ]


def average_indiv(population):
    """ :return: Zwraca 'średniego' osobnika. """
    res = numpy.average(population, axis=0)
    if type(res) == numpy.float64:
        return []
    return list(res)


def rank(individuals: 'Iterator Individual', calc_objective):
    """
    :param individuals: Grupa indywiduów.
    :param calc_objective: Określa jak otrzymać wektor wyników.
    :return: Itertator: posortowane dane wejściowe od najlepszych do najgorszych.
    """
    return iter(indiv
                for eqv_class
                in paretofront_layers(individuals,
                                      fitfun_res=calc_objective)
                for indiv
                in eqv_class
    )


def get_indivs_inorder(self, fitnesses, population):
    """ :return: Iterator: bieżąca populacja posortowana od najlepszych do najgorszych. """

    def calc_objective(ind):
        return [f(ind)
                for f
                in fitnesses
        ]

    return rank(population, calc_objective)

if __name__ == '__main__':
    start = [0.5, 0.5]
    dims = [(0.0, 1.0), (0.0, 1.0)]
    import constants
    eta_mut = constants.ETA_MUTATION_0
    rate = 1.0 / len(dims)
    mutated = [mutate(start, dims, rate, eta_mut) for _ in range(100)]
    import matplotlib.pyplot as plt
    plt.scatter([x[0] for x in mutated], [x[1] for x in mutated])
    plt.xlim(0.0, 1.0)
    plt.ylim(0.0, 1.0)
    print(start)
    plt.show()

    start_a = [0.2, 0.2]
    start_b = [0.8, 0.8]
    dims = [(0.0, 1.0), (0.0, 1.0)]
    eta_cross = constants.ETA_CROSSOVER_0
    rate = 0.9
    mutated = [crossover(start_a, start_b, dims, rate, eta_mut) for _ in range(100)]
    import matplotlib.pyplot as plt
    plt.scatter([x[0] for x in mutated], [x[1] for x in mutated])
    plt.xlim(0.0, 1.0)
    plt.ylim(0.0, 1.0)
    print(start_a)
    print(start_b)
    plt.show()
