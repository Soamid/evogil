from abc import ABC, abstractmethod

from algorithms.FVMOEA.population import Individual, Dimensions
from algorithms.base.drivertools import mutate


class Mutation(ABC):
    @abstractmethod
    def __call__(self, individual: Individual, dimensions: Dimensions) -> Individual:
        pass


class PolynomialMutation(Mutation):
    def __init__(self, probability, distribution_index):
        self.probability = probability
        self.distribution_index = distribution_index

    def __call__(self, individual: Individual, dimensions: Dimensions) -> Individual:
        mutated_vector = \
            tuple(
                mutate(
                    individual.vector, dimensions,
                    self.probability, self.distribution_index
                )
            )

        return Individual(mutated_vector)
