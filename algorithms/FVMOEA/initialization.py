import random
from abc import ABC, abstractmethod
from typing import Tuple

from algorithms.FVMOEA.population import Individual
from algorithms.FVMOEA.problem import Problem


class Initialization(ABC):
    @abstractmethod
    def __call__(self, problem: Problem) -> Individual:
        pass


class UniformInitialization(Initialization):
    def __call__(self, problem: Problem) -> Individual:
        individual_vector = tuple(
            random.uniform(lower_limit, upper_limit)
            for lower_limit, upper_limit in problem.dims
        )  # type: Tuple[float]

        return Individual(individual_vector)
