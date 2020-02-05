import copy
import logging
import random
import math

from algorithms.base.driver import Driver


class SMPSO(Driver):
    ETA = 0.0075

    def __init__(
        self,
        population,
        fitnesses,
        dims,
        mutation_eta,
        mutation_rate,
        crossover_eta,
        crossover_rate,
        w_factor,
        C1,
        C2,
        mutation_probability,
        mutate_low,
        mutate_up,
        search_space_size,
        trim_function=lambda x: x,
        fitness_archive=None,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.fitnesses = fitnesses
        self.dims = dims
        self.individuals = [Individual(trim_function(x)) for x in population]

        # Constants for velocity calcualtions
        self.w_factor = w_factor
        self.C1 = C1
        self.C2 = C2
        fi = self.C1 + self.C2 if self.C1 + self.C2 > 4.0 else 4.0
        self.constriction_coeff = 2 / (2 - fi - math.sqrt(fi * fi - 4.0 * fi))

        # Constants for polynomial mutation
        self.mutation_probability = mutation_probability
        self.mutation_eta = mutation_eta
        self.mutate_low = mutate_low
        self.mutate_up = mutate_up

        # Constatnts for search space boundaries
        self.search_space_size = search_space_size
        upper_limit = self.search_space_size
        lower_limit = -self.search_space_size
        self.delta = (upper_limit - lower_limit) / 2

        self.trim_function = trim_function
        self.leaders_size = len(population)
        self.crowding_selector = CrowdingTournament()
        self.archive = Archive(self.ETA)
        self.leader_archive = LeaderArchive(self.leaders_size)
        self.fitness_archive = fitness_archive

        self.init()

    @property
    def population(self):
        return [i.value for i in self.individuals]

    @population.setter
    def population(self, pop):
        self.individuals = [Individual(i) for i in pop]

    def init_personal_best(self):
        for i in self.individuals:
            i.best_val = copy.deepcopy(i)

    def init(self):
        self.logger = logging.getLogger(__name__)
        self.cost = 0
        self.gen_no = 0
        self.cost += self.calculate_objectives()
        self.init_leaders()
        self.init_personal_best()
        self.leader_archive.crowding()

    def init_leaders(self):
        for i in self.individuals:
            if self.leader_archive.add(copy.deepcopy(i)):
                self.archive.add(copy.deepcopy(i))

    def finalized_population(self):
        return [i.value for i in self.archive]

    def step(self):
        self.compute_speed()
        self.move()
        self.mutate()

        for i in self.individuals:
            i.value = self.trim_function(i.value)

        self.cost += self.calculate_objectives()

        self.update_leaders()
        self.update_personal_best()
        self.leader_archive.crowding()

        self.logger.debug(
            "{}: {} : {}".format(
                self.gen_no, len(self.leader_archive.archive), len(self.archive.archive)
            )
        )
        self.gen_no += 1

    def update_personal_best(self):
        for i in self.individuals:
            if i.dominates(i.best_val):
                i.best_val = copy.deepcopy(i)

    def update_leaders(self):
        for i in self.individuals:
            new_ind = copy.deepcopy(i)
            if self.leader_archive.add(new_ind):
                self.archive.add(copy.deepcopy(i))

    def calculate_objectives(self):
        objectives_cost = 0
        for i in self.individuals:
            if (self.fitness_archive is not None) and (i.value in self.fitness_archive):
                i.objectives = self.fitness_archive[i.value]
                objectives_cost = 0
            else:
                i.objectives = [o(i.value) for o in self.fitnesses]
                objectives_cost = len(self.individuals)
        return objectives_cost

    def move(self):
        for i in self.individuals:
            for d in range(len(self.dims)):
                new_x = i.value[d] + i.speed[d]
                bounded_x = max(new_x, self.dims[d][0])
                bounded_x = min(bounded_x, self.dims[d][1])

                if bounded_x != new_x:
                    i.speed[d] *= -1

                i.value[d] = bounded_x

    def compute_speed(self):
        for i in self.individuals:
            best_global = (
                self.crowding_selector(self.leader_archive)
                if len(self.leader_archive.archive) > 1
                else self.leader_archive.archive[0]
            )

            for d in range(len(self.dims)):
                i.speed[d] = self.w_factor * i.speed[d]
                + self.C1 * random.uniform(0, 1) * (i.best_val.value[d] - i.value[d])
                + self.C2 * random.uniform(0, 1) * (best_global.value[d] - i.value[d])
                i.speed[d] = self.constriction_coeff * i.speed[d]
                if i.speed[d] > self.delta:
                    i.speed[d] = self.delta
                elif i.speed[d] <= -self.delta:
                    i.speed[d] = -self.delta

    def mutate(self):
        pop_len = len(self.individuals)
        pop_part = int(pop_len / 3)
        polynomial_mutation = PolynomialMutation(
            self.mutation_probability,
            self.dims,
            self.mutation_eta,
            self.mutate_low,
            self.mutate_up
        )
        map(polynomial_mutation, self.individuals[0:pop_part])


class Mutation(object):
    def __init__(self, mutation_probability, dims):
        self.dims = dims
        self.mutation_probability = mutation_probability

    def do_mutation(self, p, index):
        return 0

    def __call__(self, i):
        for d in range(len(self.dims)):
            if random.random() < self.mutation_probability:
                mutation = self.do_mutation(i, d)
                i.value[d] += min(max(mutation, self.low), self.up)


class PolynomialMutation(Mutation):
    def __init__(
        self, eta, low, up, mutation_probability, dims
    ):
        super().__init__(mutation_probability, dims)
        self.eta = eta
        self.low = low
        self.up = up

    def do_mutation(self, i, d):
        current = i.value[d]
        u = random.random()
        mut_pow = 1.0 / (self.eta + 1.)

        if u <= 0.5:
            xy = 1.0 - ((current - self.low) / (self.up - self.low))
            val = 2.0 * u + (1.0 - 2.0 * u) * xy ** (self.eta + 1)
            delta = val ** mut_pow - 1.0
            current = current + delta * (self.up - self.low)
        else:
            xy = 1.0 - ((self.up - current) / (self.up - self.low))
            val = 2.0 * (1.0 - u) + 2.0 * (u - 0.5) * xy ** (self.eta + 1)
            delta = 1.0 - val ** mut_pow
            current = current + delta * (self.up - self.low)

        return current


class CrowdingTournament:
    def __init__(self, tournament_size=2):
        self.tournament_size = tournament_size

    def __call__(self, pool):
        sub_pool = random.sample(pool.archive, self.tournament_size)
        return min(sub_pool, key=lambda x: x.crowd_val)


class Individual:
    def __init__(self, value):
        self.value = value
        self.best_val = None
        self.crowd_val = 0
        self.objectives = []
        self.reset_speed()

    def __deepcopy__(self, memo):
        dup = Individual(copy.deepcopy(self.value, memo))
        dup.best_val = copy.deepcopy(self.best_val, memo)
        dup.speed = copy.deepcopy(self.speed, memo)
        dup.crowd_val = self.crowd_val
        dup.objectives = copy.deepcopy(self.objectives, memo)
        return dup

    def dominates(self, p2, eta=0):
        at_least_one = False
        for i in range(len(self.objectives)):
            if p2.objectives[i] < self.objectives[i] / (1 + eta):
                return False
            elif p2.objectives[i] > self.objectives[i] / (1 + eta):
                at_least_one = True

        return at_least_one

    def reset_speed(self):
        self.speed = [0] * len(self.value)

    def equal_obj(self, i):
        for o in range(len(self.objectives)):
            if self.objectives[o] != i.objectives[o]:
                return False
        return True


class Archive(object):
    def __init__(self, eta=0.0):
        self.archive = []
        self.eta = eta

    def __iter__(self):
        return self.archive.__iter__()

    def add(self, i):

        for l in self.archive:
            if l.dominates(i, self.eta):
                return False
            elif i.dominates(l, self.eta):
                self.archive.remove(l)
            elif l.equal_obj(i):
                return False

        self.archive.append(i)
        return True


class LeaderArchive(Archive):
    def __init__(self, size):
        super().__init__()
        self.size = size

    def add(self, i):
        added = super().add(i)
        if added and len(self.archive) > self.size:
            self.prune()
        return added

    def prune(self):
        self.crowding()
        worst_res = max(self.archive, key=lambda x: x.crowd_val)
        self.archive.remove(worst_res)

    def crowding(self):
        for i in self.archive:
            i.crowd_val = 0

        obj_n = len(self.archive[0].objectives)

        archive_len = len(self.archive)
        for i in range(obj_n):
            self.archive.sort(key=lambda x: x.objectives[i])
            obj_min = self.archive[0].objectives[i]
            obj_max = self.archive[archive_len - 1].objectives[i]

            self.archive[0].crowd_val = float("inf")
            self.archive[archive_len - 1].crowd_val = float("inf")

            for j in range(1, archive_len - 1):
                if obj_max - obj_min > 0:
                    dist = (
                        self.archive[j].objectives[i]
                        - self.archive[j - 1].objectives[i]
                    )
                    dist /= obj_max - obj_min
                    self.archive[j].crowd_val += dist
                else:
                    self.archive[j].crowd_val = float("inf")
