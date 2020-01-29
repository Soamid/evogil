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
        mutation_perturbation=0.5,
        mutation_probability=0.05,
        trim_function=lambda x: x,
        fitness_archive=None,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.population = population
        self.fitnesses = fitnesses
        self.dims = dims

        self.mutation_probability = mutation_probability

        self.leaders_size = len(population)  # parameter?
        self.mutation_perturbation = mutation_perturbation
        self.trim_function = trim_function
        self.fitness_archive = fitness_archive

        self.logger = logging.getLogger(__name__)
        self.search_space_size = 10
        self.leaders_archive_size = 5

        #constatns for velocity calcualtions
        self.w_factor = 1.0
        self.C1 = 2.5
        self.C2 = 2.5
        fi = self.C1 + self.C2 if self.C1 + self.C2 > 4.0 else 4.0
        self.constriction_coeff = 2 / (2 - fi - math.sqrt(fi * fi - 4.0 * fi))

        # Constants for mutation
        self.eta = 1
        self.mutate_low = 1
        self.mutate_up = 1

        #not sure if that below is correct, I assumed same search space for each dimension
        upper_limit = self.search_space_size
        lower_limit = -self.search_space_size
        self.delta = (upper_limit - lower_limit) / 2

        self.individuals = [Individual(trim_function(x), range(len(dims))) for x in population]
        self.leaders_archive = [[0. for x in range(len(dims))] for y in range(self.leaders_archive_size)]
        self.leaders_stored_results = [math.inf] * self.leaders_archive_size

        self.initialize_swarm()
        self.update_leaders_archive()

        self.gen_no = 0

    """ Overriden for being able to return final results of algorithm"""
    def finalized_population(self):
        return self.leaders_archive

    """ Overriden for being able to run one step of algorithm"""
    def step(self):
        self.compute_speed()
        self.update_position()
        self.update_leaders_archive()
        self.update_particles_memory()
        #self.logger.debug("{}: {} : {}".format(len(self.leaders_archive)))

        self.logger.error(
            "{}: ".format(
                self.gen_no)

        )
        self.gen_no += 1

    def initialize_swarm(self):
        for i in self.individuals:
            i.initialize(self.search_space_size, self.delta)

    def get_position_in_leaders_list(self, val):
        for j in range(self.leaders_archive_size):
            if val < self.leaders_stored_results[j]:
                return j
        return -1

    #can be used also as initializeLeadersArchive
    def update_leaders_archive(self):
        for i in range(len(self.population)):
            val = self.individuals[i].calculate_benchmark()
            pos = self.get_position_in_leaders_list(val)
            if pos == -1:
                continue
            self.leaders_stored_results = self.leaders_stored_results[:pos] + [val] + self.leaders_stored_results[pos:-1]
            #probably might be done better, but i can't speak pytong very well
            l = self.leaders_archive.copy()
            l[:pos] = self.leaders_archive[:pos]
            l[pos] = self.individuals[i].value
            l[pos+ 1:] = self.leaders_archive[pos:-1]
            self.leaders_archive = l
            #print(leaders_stored_results)
            #print(leaders_archive)

    def compute_speed(self):
        for i in self.individuals:
            i.compute_speed(self.w_factor, self.C1, self.C2, self.leaders_archive, self.constriction_coeff, self.delta)

    def update_position(self):
        for i in self.individuals:
            i.move()

    """ Polynomial mutation on 15% of particles """
    def mutate(self):
        for i in self.individuals:
            i.mutate(self.eta, self.mutate_low, self.mutate_up)

    """To apply and recalculate objective values after moved"""
    def update_particles_memory(self):
        for i in self.individuals:
            i.trim_position(self.trim_function)
            i.update_objectives(self.fitnesses)
            i.update_personal_best(self.fitnesses)


class Individual:

    def __init__(self, value, dims):
        self.dims = dims
        self.objectives = []
        self.value = value
        self.velocity = [0. for x in range(len(dims))]
        self.pbest = [0. for x in range(len(dims))]

    """This wasn't described, but without any initialization velocities will stay equal to 0 forever"""
    def initialize(self, search_space_size, delta):
        for d in range(len(self.dims)):
            #self.position[i] = random.uniform(-search_space_size, search_space_size)
            self.pbest[d] = self.value[d]
            self.velocity[d] = random.uniform(-delta, delta)

    def compute_speed(self, w_factor, C1, C2, leaders_archive, constriction_coeff, delta):
        for d in range(len(self.dims)):
            self.velocity[d] = w_factor * self.velocity[d]
            + C1 * random.uniform(0, 1) * (self.pbest[d] - self.value[d])
            + C2 * random.uniform(0, 1) * (leaders_archive[0][d] - self.value[d])
            self.velocity[d] = constriction_coeff * self.velocity[d]
            if self.velocity[d] > delta:
                self.velocity[d] = delta
            elif self.velocity[d] <= -delta:
                self.velocity[d] = -delta

    def move(self):
        for d in range(len(self.dims)):
            self.value[d] = self.value[d] + self.velocity[d]

    def trim_position(self, trim_function):
        self.value = trim_function(self.value)

    def update_objectives(self, fitnesses):
        self.objectives = [o(self.value) for o in fitnesses]

    def update_personal_best(self, fitnesses):
        val = self.calculate_benchmark()
        best_val = sum([o(self.pbest) for o in fitnesses])

        if val < best_val:
            self.pbest = self.value

    def mutate(self, eta, low, up):
        for d in range(len(self.dims)):
            if random.random() <= 0.15:
                current = self.value[d]
                u = random.random()
                mut_pow = 1.0 / (eta + 1.)

                if u <= 0.5:
                    xy = 1.0 - ((current - low) / (up - low))
                    val = 2.0 * u + (1.0 - 2.0 * u) * xy ** (eta + 1)
                    delta = val ** mut_pow - 1.0
                    current = current + delta * (up - low)
                else:
                    xy = 1.0 - ((up - current) / (up - low))
                    val = 2.0 * (1.0 - u) + 2.0 * (u - 0.5) * xy ** (eta + 1)
                    delta = 1.0 - val ** mut_pow
                    current = current + delta * (up - low)

                current = min(max(current, low), up)
                self.value[d] = current

    def calculate_benchmark(self):
        return sum(self.objectives) # Or dominates like in OMOPSO?

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
