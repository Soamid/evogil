import random

import numpy as np

from algorithms.base.drivergen import DriverGen


class RHGS(DriverGen):
    def __init__(self,
                 population,
                 dims,
                 fitnesses,
                 driver,
                 mutation_etas,
                 crossover_etas,
                 mutation_rates,
                 crossover_rates,
                 metaepoch_len=5,
                 max_level=2,
                 max_sprouts_no=20,
                 population_sizes=(64, 16, 4),
                 scaling_coefficients=(4096.0, 128.0, 1.0)):
        super().__init__()

        self.driver = driver

        self.dims = dims
        self.fitnesses = fitnesses

        self.metaepoch_len = metaepoch_len
        self.max_level = max_level
        self.max_sprouts_no = max_sprouts_no

        self.mutation_etas = mutation_etas
        self.mutation_rates = mutation_rates
        self.crossover_etas = crossover_etas
        self.crossover_rates = crossover_rates
        self.population_sizes = population_sizes
        self.scaling_ceofficients = scaling_coefficients

        self.root = RHGS.Node(self, 0, random.sample(population, self.population_sizes[0]))
        self.nodes = [self.root]

        self.cost = 0

    def next_step(self):
        self.run_metaepoch()
        self.trim_sprouts()
        self.release_new_sprouts()

    def run_metaepoch(self):
        for node in self.nodes:
            node.run_metaepoch()

    def trim_sprouts(self):
        for node in self.nodes:
            node.run_metaepoch()

    def release_new_sprouts(self):
        pass

    class Node():
        def __init__(self,
                     owner,
                     level,
                     population):
            self.owner = owner
            self.level = level
            self.driver = owner.driver(population=population,
                                       dims=owner.dims,
                                       fitnesses=owner.fitnesses,
                                       mutation_etas=owner.mutation_etas[self.level],
                                       mutation_rate=owner.mutation_rates[self.level],
                                       crossover_etas=owner.crossover_etas[self.level],
                                       crossover_rate=owner.crossover_rates[self.level])
            self.population = []
            self.sprouts = []

        def run_metaepoch(self):
            iterations = 0
            final_proxy = None
            for proxy in self.driver.population_generator():
                if not iterations < self.owner.metaepoch_len:
                    break
                self.owner.cost += proxy.cost
                final_proxy = proxy
                iterations += 1
            self.population = final_proxy.finalized_population()


def scaled_domain(dims, eta):
    return [(0, (b - a) / eta) for a, b in dims]


def code(xs, eta, dims):
    return [eta * x + a for x, (a, b) in zip(xs, dims)]


def code_all(vectors, eta, dims):
    return [code(xs, eta, dims) for xs in vectors]


def decode(xs, eta, dims):
    return [(x - a) / eta for x, (a, b) in zip(xs, dims)]


def decode_all(vectors, eta, dims):
    return [decode(xs, eta, dims) for xs in vectors]


def scale(xs, eta_from, eta_to):
    return [(eta_from / eta_to) * x for x in xs]


def scale_all(vectors, eta_from, eta_to):
    return [scale(xs, eta_from, eta_to) for xs in vectors]


def compare(pop_a, pop_b, variances_multiplier=2.0):
    mean_pop_a = np.mean(pop_a, axis=0)
    mean_pop_b = np.mean(pop_b, axis=0)

    diff_vector = mean_pop_b - mean_pop_a
    len_diff_vector = np.linalg.norm(diff_vector)
    diff_vector /= len_diff_vector

    projections_a = [np.dot((x - mean_pop_a), diff_vector) for x in pop_a]
    projections_std_a = np.std(projections_a)
    projections_b = [np.dot((x - mean_pop_b), diff_vector) for x in pop_b]
    projections_std_b = np.std(projections_b)

    return (variances_multiplier * projections_std_a + variances_multiplier * projections_std_b) > len_diff_vector


def __compare_test():
    sample_pop_a = [[random.gauss(0.3, 0.015), random.gauss(0.3, 0.05)]
                    for _ in range(1000)]
    import matplotlib.pyplot as plt
    # plt.scatter([x[0] for x in sample_pop_a], [x[1] for x in sample_pop_a], c='b')

    mean_pop_a = np.mean(sample_pop_a, axis=0)
    plt.scatter([mean_pop_a[0]], [mean_pop_a[1]], c='g')
    plt.scatter([mean_pop_a[0] + 2 * 0.015], [mean_pop_a[1]], c='g')
    plt.scatter([mean_pop_a[0] - 2 * 0.015], [mean_pop_a[1]], c='g')
    plt.scatter([mean_pop_a[0]], [mean_pop_a[1] + 2 * 0.05], c='g')
    plt.scatter([mean_pop_a[0]], [mean_pop_a[1] - 2 * 0.05], c='g')

    sample_pop_b = [[random.gauss(0.5, 0.04), random.gauss(0.5, 0.025)]
                    for _ in range(1000)]
    # plt.scatter([x[0] for x in sample_pop_b], [x[1] for x in sample_pop_b], c='r')

    mean_pop_b = np.mean(sample_pop_b, axis=0)
    plt.scatter([mean_pop_b[0]], [mean_pop_b[1]], c='g')
    plt.scatter([mean_pop_b[0] + 2 * 0.04], [mean_pop_b[1]], c='g')
    plt.scatter([mean_pop_b[0] - 2 * 0.04], [mean_pop_b[1]], c='g')
    plt.scatter([mean_pop_b[0]], [mean_pop_b[1] + 2 * 0.025], c='g')
    plt.scatter([mean_pop_b[0]], [mean_pop_b[1] - 2 * 0.025], c='g')

    diff_vector = mean_pop_b - mean_pop_a
    print(diff_vector)
    ax = plt.axes()
    # ax.arrow(mean_pop_a[0], mean_pop_a[1], diff_vector[0],diff_vector[1], head_width=0.0, head_length=0.0, fc='r', ec='r')

    len_diff_vector = np.linalg.norm(diff_vector)
    diff_vector /= len_diff_vector
    print(diff_vector)
    print(diff_vector[0] ** 2 + diff_vector[1] ** 2)

    dots_a = [np.dot((x - mean_pop_a), diff_vector) for x in sample_pop_a]
    flatted_a = [d * diff_vector + mean_pop_a for d in dots_a]
    # print(dots_a)
    # plt.scatter([x[0] for x in flatted_a], [x[1] for x in flatted_a], c='k')

    # for i, x in enumerate(sample_pop_a):
    # arr = flatted_a[i] - x
    # ax.arrow(x[0], x[1], arr[0], arr[1], head_width=0.0, head_length=0.0, fc='y', ec='y')

    dots_std_a = np.std(dots_a)
    print(dots_std_a)

    var_a = mean_pop_a + (2 * dots_std_a * diff_vector)
    plt.scatter([var_a[0]], [var_a[1]], c='c')

    dots_b = [np.dot((x - mean_pop_b), diff_vector) for x in sample_pop_b]
    flatted_b = [d * diff_vector + mean_pop_b for d in dots_b]
    # print(dots_b)
    # plt.scatter([x[0] for x in flatted_b], [x[1] for x in flatted_b], c='k')

    dots_std_b = np.std(dots_b)
    print(dots_std_b)

    var_b = mean_pop_b + (-2 * dots_std_b * diff_vector)
    plt.scatter([var_b[0]], [var_b[1]], c='m')

    print(len_diff_vector)
    print(2 * dots_std_a + 2 * dots_std_b)
    effect = (2 * dots_std_a + 2 * dots_std_b) > len_diff_vector
    print(effect)

    # plt.xlim([0.0, 1.0])
    # plt.ylim([0.0, 1.0])
    plt.grid(True)
    plt.axes().set_aspect('equal', 'datalim')
    plt.show()


def __coding_test():
    sample_dims = [(0.0, 1.0), (0.0, 1.0), (0.0, 1.0)]
    eta_0 = 4096.0
    eta_1 = 128.0
    eta_2 = 1.0
    print(scaled_domain(sample_dims, eta_0))
    print(scaled_domain(sample_dims, eta_1))
    print(scaled_domain(sample_dims, eta_2))

    points = [
        [random.uniform(a, b) for a, b in sample_dims]
        for _ in range(1)
    ]
    print(points)
    decoded = decode_all(points, eta_0, sample_dims)
    print(decoded)
    coded = code_all(decoded, eta_0, sample_dims)
    print(coded)
    a = 13.45123412341234123412341234
    print(a)
    a /= 10 ** 25
    print(a)
    a *= 10 ** 25
    print(a)


if __name__ == '__main__':
    __compare_test()