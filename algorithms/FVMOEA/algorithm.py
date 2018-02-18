from abc import ABC, abstractmethod
from collections import defaultdict
from operator import itemgetter, attrgetter
from typing import List

from algorithms.FVMOEA.crossover import Crossover
from algorithms.FVMOEA.indicators import Indicator, worse
from algorithms.FVMOEA.initialization import Initialization
from algorithms.FVMOEA.mutation import Mutation
from algorithms.FVMOEA.population import Population, Individual, Vector, Objectives
from algorithms.FVMOEA.problem import Problem
from algorithms.FVMOEA.selection import dominates, Selection
from algorithms.base import hv
from metrics.metrics_utils import filter_not_dominated


class Algorithm(ABC):
    def __init__(self, problem: Problem, indicators: List[Indicator]):
        self.problem = problem
        self.indicators = indicators
        self.function_evaluations = 0

    @abstractmethod
    def run(self):
        pass

    def print_indicator_values(self, population: Population) -> None:
        print(f'Function evaluations: {self.function_evaluations}')
        population_objectives = list(map(attrgetter('objectives'), population))

        for indicator in self.indicators:
            indicator_name = indicator.__class__.__name__
            value = indicator(self.problem, population_objectives, self.function_evaluations)
            if value is not None:
                print(f'{indicator_name}: {value}')

        print('')


class FVMOEA(Algorithm):
    """
    Based on Jiang, Siwei, et al. "A simple and fast hypervolume indicator-based multiobjective
    evolutionary algorithm." IEEE Transactions on Cybernetics 45.10 (2015): 2202-2213.
    http://www3.ntu.edu.sg/home/ZhangJ/paper/fvmoea.pdf
    """
    def __init__(self,
                 problem: Problem,
                 indicators: List[Indicator],
                 initialization: Initialization,
                 selection: Selection,
                 crossover: Crossover,
                 mutation: Mutation,
                 batch_size: int,
                 population_size: int,
                 maximum_function_evaluations: int):

        super().__init__(problem, indicators)

        self.initialization = initialization
        self.selection = selection
        self.crossover = crossover
        self.mutation = mutation
        self.batch_size = batch_size
        self.population_size = population_size
        self.maximum_function_evaluations = maximum_function_evaluations

        self.function_evaluations = 0

    def run(self) -> Population:
        self.function_evaluations = 0
        population = self.initialize_population()
        self.evaluate_population(population)
        self.print_indicator_values(population)

        while self.function_evaluations <= self.maximum_function_evaluations:
            population = self.algorithm_step(population)

        return population

    def initialize_population(self) -> Population:
        population = {
            self.initialization(self.problem)
            for _ in range(self.population_size)
        }

        return population

    def evaluate_population(self, population: Population) -> None:
        for individual in population:
            self.problem.evaluate(individual)
            self.function_evaluations += 1

    def algorithm_step(self, population: Population) -> Population:
        offspring = set()

        for _ in range(self.batch_size):
            offspring_solutions = self.generate(population)
            for individual in offspring_solutions:
                self.problem.evaluate(individual)
                offspring.add(individual)
                self.function_evaluations += 1

        population = self.select_offspring_population(population | offspring)
        self.print_indicator_values(population)
        return population

    def generate(self, population: Population) -> List[Individual]:
        parent_1 = self.selection(population)
        parent_2 = self.selection(population)
        offspring = self.crossover(parent_1, parent_2, self.problem.dims)
        offspring = [self.mutation(individual, self.problem.dims) for individual in offspring]
        return offspring

    def select_offspring_population(self, offspring_population: Population) -> Population:
        population_1, next_front = self.select_by_pareto_dominance(offspring_population)

        required_size = self.population_size - len(population_1)
        objectives = list(map(attrgetter('objectives'), next_front))
        reference_point = worse(objectives)
        population_2 = select_by_fast_hyper_volume(next_front, reference_point, required_size)

        population = population_1 | population_2
        return population

    def select_by_pareto_dominance(self, population: Population) -> (Population, Population):
        fronts = non_dominated_sort(population)

        next_front = set()
        selected_population = set()
        for next_front in fronts:
            if len(selected_population) + len(next_front) >= self.population_size:
                break

            selected_population.update(next_front)

        return selected_population, next_front


def non_dominated_sort(population: Population) -> List[Population]:
    dominated_by = defaultdict(set)
    how_many_dominates = defaultdict(int)
    fronts = defaultdict(set)
    front_index = 0

    for x in population:
        for y in population:
            if dominates(x, y):
                dominated_by[x].add(y)

            elif dominates(y, x):
                how_many_dominates[x] += 1

        if how_many_dominates[x] == 0:
            fronts[front_index].add(x)

    while len(fronts[front_index]) != 0:
        for x in fronts[front_index]:
            for y in dominated_by[x]:
                how_many_dominates[y] -= 1

                if how_many_dominates[y] == 0:
                    fronts[front_index + 1].add(y)

        front_index += 1

    enumerated_fronts = sorted(fronts.items(), key=itemgetter(0))
    return [front for i, front in enumerated_fronts]


def select_by_fast_hyper_volume(population: Population, reference_point: Vector, required_size: int) -> Population:
    # TODO: optimize this function, it's slow for large populations
    hyper_volume = lambda x: -hv.HyperVolume(reference_point).compute(x)
    hyper_volume_contributions = {}

    for individual in population:
        non_dominated_worse_set = \
            non_dominated_worse(individual.objectives, population - {individual})

        hyper_volume_contributions[individual] = \
            hyper_volume([individual.objectives]) - hyper_volume(non_dominated_worse_set)

    while len(population) > required_size:
        smallest_contribution_solution = min(
            hyper_volume_contributions,
            key=hyper_volume_contributions.get
        )  # type: Individual

        for individual in population - {smallest_contribution_solution}:
            worse_solution = worse([smallest_contribution_solution.objectives, individual.objectives])

            non_dominated_worse_set = \
                non_dominated_worse(worse_solution, population - {smallest_contribution_solution, individual})

            pair_hyper_volume_contribution = \
                hyper_volume([worse_solution]) - hyper_volume(non_dominated_worse_set)

            hyper_volume_contributions[individual] += pair_hyper_volume_contribution

        population.remove(smallest_contribution_solution)
        hyper_volume_contributions.pop(smallest_contribution_solution)

    return population


def non_dominated_worse(solution: Vector, population: Population) -> Objectives:
    worse_set = [
        worse([solution, individual.objectives])
        for individual in population
    ]

    return filter_not_dominated(worse_set)
