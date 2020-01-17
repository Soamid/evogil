from abc import ABC, abstractmethod
from typing import List

from algorithms.FVMOEA.population import Individual, Dimensions
from algorithms.base.drivertools import crossover


class Crossover(ABC):
    @abstractmethod
    def __call__(self, parent_1: Individual, parent_2: Individual, dimensions: Dimensions) -> List[Individual]:
        pass


class SBXCrossover(Crossover):
    def __init__(self, probability: float, distribution_index: float):
        self.probability = probability
        self.distribution_index = distribution_index

    def __call__(self, parent_1: Individual, parent_2: Individual, dimensions: Dimensions) -> List[Individual]:
        offspring_vectors = crossover(
            parent_1.vector, parent_2.vector, dimensions,
            self.probability, self.distribution_index
        )

        return [Individual(tuple(vector)) for vector in offspring_vectors]
