import collections
import math
import random

import numpy
import numpy.linalg

from algorithms.base.drivergen import ImgaProxy, Driver

EPSILON = numpy.finfo(float).eps

import matplotlib.pyplot as plt


class NSGAIII(Driver):
    class NSGAIIIImgaProxy(ImgaProxy):
        def __init__(self, driver, cost, fronts, individuals):
            super().__init__(driver, cost)
            self.individuals = individuals
            self.fronts = fronts

        def finalized_population(self):
            return [x.v for x in self.individuals]

        def current_population(self):
            return [x.v for x in self.individuals]

        def deport_emigrants(self, immigrants):
            immigrants_cp = list(immigrants)
            to_remove = []

            for p in self.individuals:
                if p.v in immigrants_cp:
                    to_remove.append(p)
                    immigrants_cp.remove(p.v)

            for p in to_remove:
                self.individuals.remove(p)
            return to_remove

        def assimilate_immigrants(self, emigrants):
            self.individuals.extend(emigrants)

        def nominate_delegates(self):
            return [x.v for x in self.fronts[1]]

    def __init__(self,
                 population,
                 dims,
                 fitnesses,
                 mutation_eta,
                 crossover_eta,
                 mutation_rate='default',
                 crossover_rate=0.9,
                 theta=5,
                 trim_function=lambda x: x,
                 fitness_archive=None):
        super().__init__()

        self.fitness_archive = fitness_archive
        self.theta = theta

        self.dims = dims
        self.dims_no = len(dims)
        self.objectives = fitnesses
        self.objective_no = len(self.objectives)

        self.eta_crossover = crossover_eta
        self.eta_mutation = mutation_eta
        self.crossover_rate = crossover_rate
        self.mutation_rate = 1.0 / len(self.dims) if mutation_rate is 'default' else mutation_rate

        self.population_size = len(population)
        self.reference_points = self.generate_reference_points()
        self.reference_point_lengths = [numpy.linalg.norm(point) for point in self.reference_points]

        self.individuals = []
        self.trim_function = trim_function
        self.population = [self.trim_function(x) for x in population]

        self.cost = 0
        self.primary_cost_included = False
        self.budget = None

        self.ideal_point = [float('inf') for _ in range(self.objective_no)]
        self.update_ideal_point(self.individuals)

        # TODO: remove debug
        # plt.scatter([x.v[0] for x in self.individuals], [x.v[1] for x in self.individuals], c='g')
        # plt.scatter([x.objectives[0] for x in self.individuals], [x.objectives[1] for x in self.individuals], c='b')
        # plt.scatter([self.ideal_point[0]], [self.ideal_point[1]], c='r')
        # plt.show()

        self.clusters = [[] for _ in self.reference_points]

    def generate_reference_points(self):
        return [generate_reference_point(self.objective_no) for _ in range(self.population_size)]

    @property
    def population(self):
        return [x.v for x in self.individuals]

    @population.setter
    def population(self, pop):
        # should work anyway, stabilize after each offspring generaion
        # if len(pop) % 2 != 0:
        # raise ValueError("Population must be even")
        # if len(pop) < len(self.reference_points):
        #     raise ValueError("Population too small for the requested amount of reference points")
        self.individuals = [Individual(x) for x in pop]
        self.population_size = len(self.individuals)

    def _calculate_objectives(self, individuals):
        for ind in individuals:
            if ind.objectives is None:
                if (self.fitness_archive is not None) and (ind.v in self.fitness_archive):
                    ind.objectives = self.fitness_archive[ind.v]
                else:
                    self.cost += 1
                    ind.objectives = [objective(ind.v) for objective in self.objectives]
                    if self.fitness_archive is not None:
                        self.fitness_archive[ind.v] = ind.objectives

    def update_ideal_point(self, individuals):
        self._calculate_objectives(individuals)
        for ind in individuals:
            for i, objective in enumerate(ind.objectives):
                if self.ideal_point[i] > objective:
                    self.ideal_point[i] = objective

    def finalized_population(self):
        return [x.v for x in self.individuals]

    def step(self):
        fronts = self.next_step()
        return self.emit_next_proxy()

    def next_step(self):
        offspring_inds = self.make_offspring_individuals()
        for ind in offspring_inds:
            ind.v = self.trim_function(ind.v)

        # TODO: remove debug
        # plt.scatter([x.v[0] for x in offspring_inds], [x.v[1] for x in offspring_inds], c='b', marker='^')
        # plt.show()

        self.update_ideal_point(offspring_inds)

        # TODO: remove debug
        # plt.scatter([x.objectives[0] for x in offspring_inds],
        # [x.objectives[1] for x in offspring_inds], c='g', marker='^')
        # plt.scatter([self.ideal_point[0]], [self.ideal_point[1]], c='r')
        # plt.show()

        offspring_inds.extend(self.individuals)
        self.normalize(offspring_inds)

        # TODO: remove debug
        # plt.scatter([x.normalized_objectives[0] for x in offspring_inds],
        #             [x.normalized_objectives[1] for x in offspring_inds])
        # plt.scatter([x[0] for x in self.reference_points], [x[1] for x in self.reference_points], c='k', marker='+')
        # plt.show()

        self.clustering(offspring_inds)

        # TODO: remove debug
        # for i, cluster in enumerate(self.clusters):
        # c = None
        # k = 7
        # if i % k == 0:
        # c = 'r'
        # elif i % k == 1:
        #         c = 'g'
        #     elif i % k == 2:
        #         c = 'b'
        #     elif i % k == 3:
        #         c = 'y'
        #     elif i % k == 4:
        #         c = 'k'
        #     elif i % k == 5:
        #         c = 'c'
        #     elif i % k == 6:
        #         c = 'm'
        #
        #     if len(cluster) > 0:
        #         plt.scatter([x.normalized_objectives[0] for x in cluster],
        #                     [x.normalized_objectives[1] for x in cluster], c=c, marker='s')
        #         plt.scatter([self.reference_points[i][0]], [self.reference_points[i][1]], c=c, marker='o', s=500)
        # plt.scatter([x[0] for x in self.reference_points], [x[1] for x in self.reference_points], c='k', marker='o')
        # plt.xlim([-0.2, 1.2])
        # plt.ylim([-0.2, 1.2])
        # plt.show()
        #
        # plt.scatter([x.objectives[0] for x in offspring_inds], [x.objectives[1] for x in offspring_inds],
        #             c='g', s=400)

        self.calculate_theta_fitness()
        fronts = theta_non_dominated_sort(offspring_inds)

        # TODO: remove debug
        # for i in fronts.keys():
        #     front = fronts[i]
        #     c = None
        #     k = 7
        #     if i == 1:
        #         c = 'r'
        #     elif i == 2:
        #         c = 'g'
        #     elif i == 3:
        #         c = 'b'
        #     elif i == 4:
        #         c = 'y'
        #     elif i == 5:
        #         c = 'm'
        #     elif i == 6:
        #         c = 'c'
        #     else:
        #         c = 'k'
        #
        # plt.scatter([x.normalized_objectives[0] for x in front], [x.normalized_objectives[1] for x in front],
        #             c=c, marker='s', s=100)
        # plt.xlim([-0.2, 1.2])
        # plt.ylim([-0.2, 1.2])
        # plt.show()

        self.create_final_population(fronts)
        return fronts

    def make_offspring_individuals(self):
        offspring_inds = []
        for _ in range(int(self.population_size / 2)):
            parent_a = random.choice(self.individuals)
            parent_b = random.choice(self.individuals)
            child_a, child_b = simulated_binary_crossover(parent_a, parent_b, self.dims,
                                                          crossover_rate=self.crossover_rate, eta=self.eta_crossover)
            polynomial_mutation(child_a, self.dims, mutation_rate=self.mutation_rate, eta=self.eta_mutation)
            polynomial_mutation(child_b, self.dims, mutation_rate=self.mutation_rate, eta=self.eta_mutation)
            offspring_inds.append(child_a)
            offspring_inds.append(child_b)
        return offspring_inds

    def normalize(self, individuals):
        defiled_point = [float('-inf') for _ in range(self.objective_no)]
        for ind in individuals:
            for i, objective in enumerate(ind.objectives):
                if defiled_point[i] < objective:
                    defiled_point[i] = objective

        # TODO: remove debug
        # plt.scatter([defiled_point[0]], [defiled_point[1]], c='r')
        # plt.show()

        for ind in individuals:
            ind.normalized_objectives = numpy.array(
                [(obj - self.ideal_point[i]) / (defiled_point[i] - self.ideal_point[i] + EPSILON)
                 for i, obj in enumerate(ind.objectives)])

    def clustering(self, individuals):
        self.clusters = [[] for _ in self.reference_points]
        for ind in individuals:
            min_rejection = float('inf')
            min_i = -1
            for i, reference_point in enumerate(self.reference_points):
                rejection = scalar_rejection(ind, reference_point, self.reference_point_lengths[i])
                if rejection < min_rejection:
                    min_rejection = rejection
                    min_i = i
            self.clusters[min_i].append(ind)
            ind.cluster = min_i
            ind.rejection = min_rejection

    def calculate_theta_fitness(self):
        for i, cluster in enumerate(self.clusters):
            for ind in cluster:
                ind.theta_fitness = scalar_projection(ind, self.reference_points[i],
                                                      self.reference_point_lengths[i]) + self.theta * ind.rejection

    def create_final_population(self, fronts):
        new_inds = []
        new_size = len(new_inds)
        i = 1
        while new_size + len(fronts[i]) <= self.population_size:
            new_inds.extend(fronts[i])
            new_size = len(new_inds)
            i += 1
        new_inds.extend(random.sample(fronts[i], self.population_size - len(new_inds)))

        # TODO remove debug
        # for front in fronts.values():
        # plt.scatter([x.v[0] for x in front], [x.v[1] for x in front], c='k', s=100)
        # plt.scatter([x.v[0] for x in new_inds], [x.v[1] for x in new_inds], c='r', s=50)
        # plt.xlim(-12, 12)
        # plt.ylim(-12, 12)
        # plt.show()
        #
        # for front in fronts.values():
        # plt.scatter([x.objectives[0] for x in front], [x.objectives[1] for x in front], c='k', s=100)
        # plt.scatter([x.objectives[0] for x in new_inds], [x.objectives[1] for x in new_inds], c='r', s=50)
        # plt.xlim(-15., 5.)
        # plt.ylim(-15., 25.)
        # plt.show()

        self.individuals = new_inds

    def finish(self):
        return [x.v for x in self.individuals]


class Individual:
    def __init__(self, vector):
        self.v = vector
        self.objectives = None


def theta_non_dominated_sort(individuals):
    dominated_by = collections.defaultdict(set)
    how_many_dominates = collections.defaultdict(int)
    nsga_rank = collections.defaultdict(int)
    front = collections.defaultdict(list)

    for x in individuals:
        for y in individuals:
            if dominates(x, y):
                dominated_by[x].add(y)
            elif dominates(y, x):
                how_many_dominates[x] += 1
        if how_many_dominates[x] == 0:
            nsga_rank[x] = 1
            front[1].append(x)

    front_no = 1
    while not len(front[front_no]) == 0:
        for x in front[front_no]:
            for y in dominated_by[x]:
                how_many_dominates[y] -= 1
                if how_many_dominates[y] == 0:
                    nsga_rank[y] = front_no + 1
                    front[front_no + 1].append(y)
        front_no += 1

    return front


def dominates(x, y):
    if x.cluster == y.cluster and x.theta_fitness < y.theta_fitness:
        return True
    else:
        return False


def generate_reference_point(objective_no):
    reference_point = []
    coord_sum = 0.0
    for i in range(1, objective_no + 1):
        if i < objective_no:
            rand = 0.0
            while rand == 0.0:
                rand = random.random()
            coordinate = (1.0 - coord_sum) * (1.0 - math.pow(rand, 1.0 / (objective_no - i)))
            coord_sum += coordinate
            reference_point.append(coordinate)
        else:
            reference_point.append(1.0 - coord_sum)
    return numpy.array(reference_point)


def scalar_projection(ind, reference_point, reference_point_length):
    return numpy.dot(ind.normalized_objectives, reference_point) / reference_point_length


def scalar_rejection(ind, reference_point, reference_point_length):
    scalar_projection_value = scalar_projection(ind, reference_point, reference_point_length)
    return numpy.linalg.norm(
        ind.normalized_objectives - ((scalar_projection_value / reference_point_length) * reference_point))


def simulated_binary_crossover(parent_a, parent_b, dims, crossover_rate=1.0, eta=30.0):
    child_a = Individual([x for x in parent_a.v])
    child_b = Individual([x for x in parent_b.v])

    if random.random() > crossover_rate:
        child_a.objectives = [x for x in parent_a.objectives]
        child_b.objectives = [x for x in parent_b.objectives]
        return child_a, child_b

    for i, dim in enumerate(dims):
        if random.random() > 0.5:
            continue
        if math.fabs(parent_a.v[i] - parent_b.v[i]) <= EPSILON:
            continue

        y1 = min(parent_a.v[i], parent_b.v[i])
        y2 = max(parent_a.v[i], parent_b.v[i])

        lb, ub = dim

        rand = random.random()

        # child a
        beta = 1.0 + (2.0 * (y1 - lb) / (y2 - y1 + EPSILON))
        alpha = 2.0 - pow(beta, -(eta + 1.0))
        beta_q = get_beta_q(rand, alpha, eta)

        child_a.v[i] = 0.5 * ((y1 + y2) - beta_q * (y2 - y1))

        # child b
        beta = 1.0 + (2.0 * (ub - y2) / (y2 - y1 + EPSILON))
        alpha = 2.0 - pow(beta, -(eta + 1.0))
        beta_q = get_beta_q(rand, alpha, eta)

        child_b.v[i] = 0.5 * ((y1 + y2) + beta_q * (y2 - y1))

        # boundary checking
        child_a.v[i] = min(ub, max(lb, child_a.v[i]))
        child_b.v[i] = min(ub, max(lb, child_b.v[i]))

        if random.random() > 0.5:
            temp = child_a.v[i]
            child_a.v[i] = child_b.v[i]
            child_b.v[i] = temp

    return child_a, child_b


def get_beta_q(rand, alpha, eta):
    if rand <= (1.0 / alpha):
        beta_q = pow((rand * alpha), (1.0 / (eta + 1.0)))
    else:
        beta_q = pow((1.0 / (2.0 - rand * alpha)), (1.0 / (eta + 1.0)))
    return beta_q


def polynomial_mutation(ind, dims, mutation_rate=0.0, eta=20.0):
    for i, dim in enumerate(dims):
        if random.random() > mutation_rate:
            continue

        y = ind.v[i]
        lb, ub = dim

        delta1 = (y - lb) / (ub - lb + EPSILON)
        delta2 = (ub - y) / (ub - lb + EPSILON)

        mut_pow = 1.0 / (eta + 1.0)

        rnd = random.random()

        if rnd <= 0.5:
            xy = 1.0 - delta1
            val = 2.0 * rnd + (1.0 - 2.0 * rnd) * (pow(xy, (eta + 1.0)))
            delta_q = pow(val, mut_pow) - 1.0
        else:
            xy = 1.0 - delta2
            val = 2.0 * (1.0 - rnd) + 2.0 * (rnd - 0.5) * (pow(xy, (eta + 1.0)))
            delta_q = 1.0 - (pow(val, mut_pow))

        y += delta_q * (ub - lb)
        y = min(ub, max(lb, y))

        ind.v[i] = y
        ind.objectives = None


if __name__ == '__main__':
    sample_dims = [(-100.0, 100.0), (-100.0, 100.0)]

    mutatedX = []
    mutatedY = []
    for _ in range(100):
        to_mut = Individual([0.0, 0.0])
        polynomial_mutation(to_mut, sample_dims, 0.9, 300.0)
        mutatedX.append(to_mut.v[0])
        mutatedY.append(to_mut.v[1])
    plt.scatter(mutatedX, mutatedY)
    plt.xlim(-100.0, 100.0)
    plt.ylim(-100.0, 100.0)

    plt.show()

    # crossX = []
    # crossY = []
    # for _ in range(10000):
    # to_crossA = Individual([-10.0, -10.0])
    #     to_crossB = Individual([10.0, 10.0])
    #     newA, newB = simulated_binary_crossover(to_crossA, to_crossB, dims, 1.0, eta=150.0)
    #     crossX.append(newA.v[0])
    #     crossY.append(newA.v[1])
    #     crossX.append(newB.v[0])
    #     crossY.append(newB.v[1])
    # plt.scatter(crossX, crossY)
    # plt.xlim(-100.0, 100.0)
    # plt.ylim(-100.0, 100.0)
    #
    # plt.show()

    # objectives = [lambda x: -10 * math.exp(-0.2 * math.sqrt(x[0] * x[0] + x[1] * x[1])),
    #               lambda x: math.pow(abs(x[0]), 0.8) + 5 * math.pow(math.sin(x[0]), 3)
    #               + math.pow(abs(x[1]), 0.8) + 5 * math.pow(math.sin(x[1]), 3)]
    # dimensions = [(-10, 10), (-10, 10)]
    # my_individuals = [[random.uniform(-10, 10), random.uniform(-10, 10)] for _ in range(250)]
    #
    # my_pop = NSGAIII(my_individuals, dimensions, objectives, theta=0)
    # # population.steps(range(100))
    #
    # for j in range(100):
    #     my_pop.next_step()
    #     print(j)
    #
    #     effect = my_pop.finish()
    #     X = [my_pop.objectives[0](x) for x in effect]
    #     Y = [my_pop.objectives[1](x) for x in effect]
    #     plt.scatter(X, Y)
    #     # pylab.xlim(-10.,250.)
    #     # pylab.ylim(-10.,250.)
    #     plt.xlim(-15., 5.)
    #     plt.ylim(-15., 25.)
    #
    #     file = ""
    #     if j < 10:
    #         file += "0"
    #     plt.savefig("pictures//" + file + str(j) + ".png")
    #     plt.clf()
