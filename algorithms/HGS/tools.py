import collections
import random
import time

import floatextras
import numpy as np

from algorithms.base import drivertools


def population_from_delegate(delegate, size, dims, rate, eta):
    population = [[x for x in delegate]]
    for _ in range(size - 1):
        population.append(drivertools.mutate(delegate, dims, rate, eta))
    return population


def redundant(pop_a, pop_b, min_dist):
    mean_pop_a = np.mean(pop_a, axis=0)
    mean_pop_b = np.mean(pop_b, axis=0)

    dist = np.linalg.norm(mean_pop_a - mean_pop_b)
    return dist < min_dist


def trim_vector(vector, bits_no):
    return [trim_mantissa(x, bits_no) for x in vector]


def trim_mantissa(value, bits_no):
    sign, digits, exponent = floatextras.as_tuple(value)
    digits = tuple([(d if i < bits_no else 0) for i, d in enumerate(digits)])
    return floatextras.from_tuple((sign, digits, exponent))


def blurred_fitnesses(level, fitnesses, fitness_errors):
    def blurred(f):
        def blurred_f(*args, **kwargs):
            f_val = f(*args, **kwargs)
            x = np.math.fabs(
                random.gauss(f_val, fitness_errors[level] * f_val / 3.0)
            )

            # print("level: {}, normal: {} blurred: {}, diff: {}".format(level, f_val, x, math.fabs(f_val - x)/f_val))
            return x

        return blurred_f

    return [blurred(f) for f in fitnesses]


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


import matplotlib.pyplot as plt


def _plot_node(node, color, dims, delegates=False):
    if not delegates:
        pop = node.population
    else:
        pop = node.delegates

    if node.alive:
        marker = "o"
    else:
        marker = "+"
    plt.scatter([x[0] for x in pop], [x[1] for x in pop], color=color, marker=marker)
    plt.xlim(dims[0][0], dims[0][1])
    plt.ylim(dims[1][0], dims[1][1])
    plt.savefig("plots/debug/{}.png".format(time.time()))
    plt.close()
