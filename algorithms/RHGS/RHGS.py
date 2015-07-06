import random

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