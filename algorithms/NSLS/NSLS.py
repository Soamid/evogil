import random

import collections
from scipy.spatial import distance

from algorithms.NSGAII import NSGAII
from algorithms.base.driver import Driver


class NSLS(Driver):
    def __init__(
        self,
        population,
        dims,
        fitnesses,
        mutation_eta,
        crossover_eta,
        mutation_rate,
        crossover_rate,
        trim_function=lambda x: x,
        fitness_archive=None,
        local_search_mu=0.5,
        local_search_sigma=0.5,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)

        self.trim_function = trim_function
        self.fitness_archive = fitness_archive

        self.dims = dims
        self.dims_no = len(dims)
        self.objectives = fitnesses
        self.objective_no = len(self.objectives)

        self.local_search_mu = local_search_mu
        self.local_search_sigma = local_search_sigma

        self.individuals = []
        self.population_size = len(population)
        self.population = [self.trim_function(x) for x in population]

        self.dominated_by = None
        self.how_many_dominates = None
        self.nsga_rank = None
        self.front = None

        self.cost = 0

    @property
    def population(self):
        return [x.v for x in self.individuals]

    @population.setter
    def population(self, pop):
        self.individuals = [Individual(x) for x in pop]
        self.population_size = len(self.individuals)

    def finalized_population(self):
        return [x.v for x in self.individuals]

    def calculate_objectives(self, individuals):
        for ind in individuals:
            if ind.objectives is None:
                if (self.fitness_archive is not None) and (
                    ind.v in self.fitness_archive
                ):
                    fitnesses = self.fitness_archive[ind.v]
                else:
                    self.cost += 1
                    fitnesses = [objective(ind.v) for objective in self.objectives]
                    if self.fitness_archive is not None:
                        self.fitness_archive[ind.v] = fitnesses
                ind.objectives = {
                    objective: fitness
                    for objective, fitness in zip(self.objectives, fitnesses)
                }

    def step(self):
        self.calculate_objectives(self.individuals)
        self.local_search()
        self.nd_sort()
        self.next_generation()

    def local_search(self):
        individuals_copy = [ind for ind in self.individuals]
        for i in range(len(individuals_copy)):
            for k in range(self.dims_no):
                ind_x = individuals_copy[i]
                c = random.gauss(self.local_search_mu, self.local_search_sigma)
                [ind_u, ind_v] = random.sample(individuals_copy, 2)
                diff = c * (ind_u.v[k] - ind_v.v[k])

                w_plus = Individual([x for x in ind_x.v])
                w_plus.v[k] += diff
                w_plus.v = self.trim_function(w_plus.v)
                if w_plus.v[k] < self.dims[k][0] or w_plus.v[k] > self.dims[k][1]:
                    w_plus.v[k] = ind_x.v[k]

                w_minus = Individual([x for x in ind_x.v])
                w_minus.v[k] -= diff
                w_minus.v = self.trim_function(w_minus.v)
                if w_minus.v[k] < self.dims[k][0] or w_minus.v[k] > self.dims[k][1]:
                    w_minus.v[k] = ind_x.v[k]

                self.calculate_objectives([w_plus, w_minus])
                plus_dominates = NSGAII.dominates(w_plus, ind_x)
                plus_dominated = NSGAII.dominates(ind_x, w_plus)
                minus_dominates = NSGAII.dominates(w_minus, ind_x)
                minus_dominated = NSGAII.dominates(ind_x, w_minus)

                if plus_dominates and minus_dominates:
                    w_final = random.choice([w_plus, w_minus])
                    individuals_copy[i] = w_final
                elif plus_dominates:
                    individuals_copy[i] = w_plus
                elif minus_dominates:
                    individuals_copy[i] = w_minus
                elif not plus_dominated and not minus_dominated:
                    w_final = random.choice([w_plus, w_minus])
                    individuals_copy[i] = w_final
                elif not plus_dominated:
                    individuals_copy[i] = w_plus
                elif not minus_dominated:
                    individuals_copy[i] = w_minus
                else:
                    pass

        for ind in individuals_copy:
            if ind not in self.individuals:
                self.individuals.append(ind)

    def nd_sort(self):
        self.dominated_by = collections.defaultdict(set)
        self.how_many_dominates = collections.defaultdict(int)
        self.nsga_rank = collections.defaultdict(int)
        self.front = collections.defaultdict(list)

        for x in self.individuals:
            for y in self.individuals:
                if NSGAII.dominates(x, y):
                    self.dominated_by[x].add(y)
                elif NSGAII.dominates(y, x):
                    self.how_many_dominates[x] += 1
            if self.how_many_dominates[x] is 0:
                self.nsga_rank[x] = 1
                self.front[1].append(x)

        front_no = 1
        while True:
            if len(self.front[front_no]) is 0:
                break
            for x in self.front[front_no]:
                for y in self.dominated_by[x]:
                    self.how_many_dominates[y] -= 1
                    if self.how_many_dominates[y] is 0:
                        self.nsga_rank[y] = front_no + 1
                        self.front[front_no + 1].append(y)
            front_no += 1

    def next_generation(self):
        next_gen_individuals = []

        front_no = 1
        while (
            len(next_gen_individuals) + len(self.front[front_no])
            <= self.population_size
        ):
            next_gen_individuals.extend(self.front[front_no])
            front_no += 1
        last_front = self.front[front_no]

        to_select = self.population_size - len(next_gen_individuals)

        additional = []
        for obj_f in self.objectives:
            min_obj = float("+inf")
            min_ind = None
            max_obj = float("-inf")
            max_ind = None
            for ind in last_front:
                obj = ind.objectives[obj_f]
                if obj < min_obj:
                    min_obj = obj
                    min_ind = ind
                if obj > max_obj:
                    max_obj = obj
                    max_ind = ind
                if min_ind not in additional:
                    additional.append(min_ind)
                if max_ind not in additional:
                    additional.append(max_ind)

        if len(additional) > to_select:
            additional = random.sample(additional, to_select)
        elif len(additional) < to_select:
            last_front = [x for x in last_front if x not in additional]
            distances = collections.defaultdict(float)
            for ind in last_front:
                distances[ind] = min(
                    [distance.euclidean(ind.v, x.v) for x in additional]
                )

            for _ in range(to_select - len(additional)):
                max_dist = float("-inf")
                max_ind = None
                for ind in last_front:
                    dist = distances[ind]
                    if dist > max_dist:
                        max_dist = dist
                        max_ind = ind
                additional.append(max_ind)
                last_front.remove(max_ind)
                for ind in last_front:
                    distances[ind] = min(
                        distances[ind], distance.euclidean(ind.v, max_ind.v)
                    )

        next_gen_individuals.extend(additional)
        self.individuals = next_gen_individuals


class Individual:
    def __init__(self, vector):
        self.v = vector
        self.objectives = None
