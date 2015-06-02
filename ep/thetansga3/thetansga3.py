import collections
import math
import random

import numpy
import numpy.linalg
import scipy.special

from ep.utils.driver import Driver


EPSILON = numpy.finfo(float).eps
random.seed()


class ThetaNSGAIII(Driver):
    def __init__(self,
                 population,
                 dims,
                 fitnesses,
                 mutation_variance,
                 crossover_variance,
                 partitions=None,
                 theta=5):
        super().__init__(population, dims, fitnesses, mutation_variance, crossover_variance)

        self.theta = theta
        self.partitions = partitions

        self.dims = dims
        self.dims_no = len(dims)
        self.objectives = fitnesses
        self.objective_no = len(self.objectives)

        self.population_size = len(population)
        if self.partitions is None:
            self.partitions = 1
            while int(scipy.special.binom(self.objective_no + self.partitions - 1.0,
                                          self.partitions)) <= self.population_size:
                self.partitions += 1
            self.partitions -= 1

        self.reference_points = self.generate_reference_points()
        self.reference_point_lengths = [numpy.linalg.norm(point) for point in self.reference_points]

        self.individuals = []
        self.population = population

        self.cost = 0
        self.primary_cost_included = False
        self.ideal_point = [float('inf') for _ in range(self.objective_no)]
        self.update_ideal_point(self.individuals)

        self.budget = None

        self.mutation_rate = 1.0 / self.dims_no

        self.clusters = [[] for _ in self.reference_points]

    def generate_reference_points(self):
        point_no = int(scipy.special.binom(self.objective_no + self.partitions - 1.0, self.partitions))
        return [generate_reference_point(self.objective_no) for _ in range(point_no)]

    @property
    def population(self):
        return [x.v for x in self.individuals]

    @population.setter
    def population(self, pop):
        if len(pop) % 2 != 0:
            raise ValueError("Population must be even")
        if len(pop) < len(self.reference_points):
            raise ValueError("Population too small for the requested amount of reference points")
        self.individuals = [Individual(x) for x in pop]
        self.population_size = len(self.individuals)

    def _calculate_objectives(self, individuals):
        for ind in individuals:
            if ind.objectives is None:
                self.cost += 1
                ind.objectives = [objective(ind.v) for objective in self.objectives]

    def update_ideal_point(self, individuals):
        self._calculate_objectives(individuals)
        for ind in individuals:
            for i, objective in enumerate(ind.objectives):
                if self.ideal_point[i] > objective:
                    self.ideal_point[i] = objective

    def steps(self, generator, budget=None):
        if self.primary_cost_included:
            self.cost = 0
        for _ in generator:
            self.next_step()
            if budget is not None and self.cost > self.budget:
                break
        self.primary_cost_included = True
        return self.cost

    def next_step(self):
        offspring_inds = self.make_offspring_individuals()
        self.update_ideal_point(offspring_inds)
        offspring_inds.extend(self.individuals)
        self.normalize(offspring_inds)
        self.clustering(offspring_inds)
        self.calculate_theta_fitness()
        fronts = theta_non_dominated_sort(offspring_inds)
        self.create_final_population(fronts)

    def make_offspring_individuals(self):
        offspring_inds = []
        for _ in range(int(self.population_size / 2)):
            parent_a = random.choice(self.individuals)
            parent_b = random.choice(self.individuals)
            child_a, child_b = simulated_binary_crossover(parent_a, parent_b, self.dims)
            polynomial_mutation(child_a, self.dims, mutation_rate=self.mutation_rate)
            polynomial_mutation(child_b, self.dims, mutation_rate=self.mutation_rate)
            offspring_inds.append(child_a)
            offspring_inds.append(child_b)
        return offspring_inds

    def normalize(self, individuals):
        defiled_point = [float('-inf') for _ in range(self.objective_no)]
        for ind in individuals:
            for i, objective in enumerate(ind.objectives):
                if defiled_point[i] < objective:
                    defiled_point[i] = objective

        for ind in individuals:
            ind.normalized_objectives = numpy.array(
                [(obj - self.ideal_point[i]) / (defiled_point[i] - self.ideal_point[i])
                 for i, obj in enumerate(ind.objectives)])

    def clustering(self, individuals):
        self.clusters = [[] for _ in self.reference_points]
        for ind in individuals:
            min_projection = float('inf')
            min_i = -1
            for i, reference_point in enumerate(self.reference_points):
                projection = scalar_projection(ind, reference_point, self.reference_point_lengths[i])
                if projection < min_projection:
                    min_projection = projection
                    min_i = i
            self.clusters[min_i].append(ind)
            ind.cluster = min_i
            ind.projection = min_projection

    def calculate_theta_fitness(self):
        for i, cluster in enumerate(self.clusters):
            for ind in cluster:
                ind.theta_fitness = ind.projection + self.theta * scalar_rejection(ind, self.reference_points[i],
                                                                                   self.reference_point_lengths[i])

    def create_final_population(self, fronts):
        new_inds = []
        new_size = len(new_inds)
        i = 1
        while new_size + len(fronts[i]) <= self.population_size:
            # print(i)
            new_inds.extend(fronts[i])
            new_size = len(new_inds)
            i += 1
        new_inds.extend(random.sample(fronts[i], self.population_size - len(new_inds)))
        self.individuals = new_inds

    def finish(self):
        print(len(self.individuals))
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


def simulated_binary_crossover(parent_a, parent_b, dims, crossover_rate=1.0, eta=30):
    child_a = Individual(parent_a.v)
    child_b = Individual(parent_b.v)

    if random.random() > crossover_rate:
        child_a.objectives = parent_a.objectives
        child_b.objectives = parent_b.objectives
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
        beta = 1.0 + (2.0 * (y1 - lb) / (y2 - y1))
        alpha = 2.0 - pow(beta, -(eta + 1.0))
        beta_q = get_beta_q(rand, alpha, eta)

        child_a.v[i] = 0.5 * ((y1 + y2) - beta_q * (y2 - y1))

        # child b
        beta = 1.0 + (2.0 * (ub - y2) / (y2 - y1))
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


def polynomial_mutation(ind, dims, mutation_rate=0.0, eta=20):
    for i, dim in enumerate(dims):
        if random.random() > mutation_rate:
            continue

        y = ind.v[i]
        lb, ub = dim

        delta1 = (y - lb) / (ub - lb)
        delta2 = (ub - y) / (ub - lb)

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
    pass