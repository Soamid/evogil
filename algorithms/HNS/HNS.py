import collections

import floatextras
import numpy as np

from algorithms.base.drivergen import DriverGen
from algorithms.base.hv import HyperVolume

EPSILON = np.finfo(float).eps


class HNS(DriverGen):
    def __init__(self,
                 population,
                 dims,
                 fitnesses,
                 driver,
                 mutation_eta,
                 crossover_eta,
                 mutation_rate,
                 crossover_rate,
                 reference_point,
                 metaepoch_len):
        super().__init__()

        self.driver = driver

        self.dims = dims
        self.reference_point = reference_point
        self.fitnesses = fitnesses

        self.metaepoch_len = metaepoch_len

        self.mutation_eta = mutation_eta
        self.mutation_rate = mutation_rate
        self.crossover_eta = crossover_eta
        self.crossover_rate = crossover_rate

        self.global_fitness_archive = ResultArchive()

        self.root = HNS.Node(self, population)

        self.cost = 0
        self.acc_cost = 0

    class HNSProxy(DriverGen.Proxy):
        def __init__(self, cost, driver):
            super().__init__(cost)
            self.cost = cost
            self.driver = driver

        def finalized_population(self):
            return self.driver.root.population

        def current_population(self):
            return self.driver.root.population

        def deport_emigrants(self, immigrants):
            raise Exception("HNS does not support migrations")

        def assimilate_immigrants(self, emigrants):
            raise Exception("HNS does not support migrations")

        def nominate_delegates(self):
            raise Exception("HNS does not support sprouting")

    def population_generator(self):
        self.acc_cost = 0
        while True:
            self.next_step()
            yield HNS.HNSProxy(self.cost, self)
            self.acc_cost += self.cost
            # print("cost", self.acc_cost, "hits", self.root.driver.archive_hits)
            self.cost = 0
        return self.acc_cost

    def next_step(self):
        self.root.run_metaepoch()
        self.root.increase_accuracy()

    class Node():
        def __init__(self,
                     owner,
                     population):
            self.owner = owner
            self.current_bits = 4
            self.driver = owner.driver(population=population,
                                       dims=owner.dims,
                                       fitnesses=owner.fitnesses,
                                       mutation_eta=owner.mutation_eta,
                                       mutation_rate=owner.mutation_rate,
                                       crossover_eta=owner.crossover_eta,
                                       crossover_rate=owner.crossover_rate,
                                       fitness_archive=self.owner.global_fitness_archive,
                                       trim_function=lambda x: trim_vector(x, self.current_bits))
            self.population = []

            self.relative_hypervolume = None
            self.old_hypervolume = float('-inf')
            self.hypervolume = float('-inf')

            self.final_proxy = None

        def run_metaepoch(self):
            iterations = 0
            self.final_proxy = None
            for proxy in self.driver.population_generator():
                self.owner.cost += proxy.cost
                self.final_proxy = proxy
                iterations += 1
                if not iterations < self.owner.metaepoch_len:
                    break
            self.population = self.final_proxy.finalized_population()
            self.update_dominated_hypervolume()

        def update_dominated_hypervolume(self):
            self.old_hypervolume = self.hypervolume
            fitness_values = [[f(p) for f in self.owner.fitnesses] for p in self.population]
            hv = HyperVolume(self.owner.reference_point)

            if self.relative_hypervolume is None:
                self.relative_hypervolume = hv.compute(fitness_values)
            else:
                self.hypervolume = hv.compute(fitness_values) - self.relative_hypervolume

        def increase_accuracy(self):
            if self.current_bits < 52:
                if self.old_hypervolume > 0.0 and ((self.hypervolume/(self.old_hypervolume + EPSILON)) - 1.0) < 0.01:
                    self.relative_hypervolume = None
                    self.old_hypervolume = float('-inf')
                    self.hypervolume = float('-inf')
                    self.current_bits *= 2

                    self.driver.trim_function = lambda x: trim_vector(x, self.current_bits)
                    coeff = 2.0
                    self.driver.mutation_eta *= coeff
                    self.driver.crossover_eta *= coeff
                    # print("increased acc", self.current_bits)


def trim_vector(vector, bits_no):
    return [trim_mantissa(x, bits_no) for x in vector]


def trim_mantissa(value, bits_no):
    sign, digits, exponent = floatextras.as_tuple(value)
    digits = tuple([(d if i < bits_no else 0) for i, d in enumerate(digits)])
    return floatextras.from_tuple((sign, digits, exponent))


class TransformedDict(collections.MutableMapping):
    """A dictionary that applies an arbitrary key-altering
       function before accessing the keys"""

    def __init__(self, *args, **kwargs):
        self.store = dict()
        self.update(dict(*args, **kwargs))  # use the free update to set keys

    def __getitem__(self, key):
        return self.store[self.__keytransform__(key)]

    def __setitem__(self, key, value):
        self.store[self.__keytransform__(key)] = value

    def __delitem__(self, key):
        del self.store[self.__keytransform__(key)]

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)

    def __keytransform__(self, key):
        return key


class ResultArchive(TransformedDict):
    def __keytransform__(self, key):
        return tuple(key)
