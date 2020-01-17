import random
from abc import ABC, abstractmethod

from algorithms.FVMOEA.population import Individual, Population


class Selection(ABC):
    @abstractmethod
    def __call__(self, population: Population) -> Individual:
        pass


class BinaryTournament2(Selection):
    population_size = 2

    def __call__(self, population: Population) -> Individual:
        sub_population = random.sample(population, self.population_size)
        individual_1, individual_2 = sub_population
        return individual_1 if dominates(individual_1, individual_2) else individual_2


def dominates(individual_1: Individual, individual_2: Individual) -> bool:
    return dominates_weak(individual_1, individual_2) and \
           not dominates_weak(individual_2, individual_1)


def dominates_weak(individual_1: Individual, individual_2: Individual) -> bool:
    return all(x <= y for x, y in zip(individual_1.objectives, individual_2.objectives))
