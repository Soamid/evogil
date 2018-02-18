import os
import time
from abc import ABC, abstractmethod
from operator import itemgetter
from typing import Tuple, Any

import seaborn
from matplotlib import pyplot

import algorithms.base.hv as hv
import metrics.epsilon as eps
from algorithms.FVMOEA.population import Objectives, Vector
from algorithms.FVMOEA.problem import Problem
from metrics.metrics_utils import generational_distance, inverse_generational_distance, spacing

seaborn.set_palette('muted')


class Indicator(ABC):
    def __init__(self, plot=False):
        self.plot = plot
        self.values_history = []
        self.evaluations_history = []

    def __call__(self, problem: Problem, objectives: Objectives, evaluations_number: int) -> Any:
        value = self.evaluate(problem, objectives)

        if self.plot:
            self.values_history.append(value)
            self.evaluations_history.append(evaluations_number)
            pyplot.plot(self.evaluations_history, self.values_history, label=self.__class__.__name__)

        return value

    @abstractmethod
    def evaluate(self, problem: Problem, objectives: Objectives) -> Any:
        pass


class HyperVolume(Indicator):
    def evaluate(self, problem: Problem, objectives: Objectives) -> Any:
        # TODO: decide what reference point to use
        reference_point = tuple(map(itemgetter(1), problem.dims))[:len(objectives[0])]
        # reference_point = worse(objectives)

        hyper_volume = hv.HyperVolume(reference_point)
        return hyper_volume.compute(objectives)


class GD(Indicator):
    def evaluate(self, problem: Problem, objectives: Objectives) -> Any:
        return generational_distance(objectives, problem.optimal_pareto)


class IGD(Indicator):
    def evaluate(self, problem: Problem, objectives: Objectives) -> Any:
        return inverse_generational_distance(objectives, problem.optimal_pareto)


class Spread(Indicator):
    def evaluate(self, problem: Problem, objectives: Objectives) -> Any:
        return spacing(objectives)


class Epsilon(Indicator):
    def evaluate(self, problem: Problem, objectives: Objectives) -> Any:
        epsilon = eps.Epsilon()
        return epsilon.epsilon(objectives, problem.optimal_pareto)


class Pareto(Indicator):
    def evaluate(self, problem: Problem, objectives: Objectives) -> Any:
        assert len(objectives[0]) == 2, \
            'Plot indicator supports only 2D objectives'

        optimal_x, optimal_y = zip(*problem.optimal_pareto)
        current_x, current_y = zip(*objectives)
        pyplot.plot(optimal_x, optimal_y, 'go', label='Optimal')
        pyplot.plot(current_x, current_y, 'bo', label='Current')


class Plot(Indicator):
    def __init__(self, show=False, save_path=None):
        super().__init__()
        self.show = show
        self.save_path = save_path

        if save_path:
            save_dir = os.path.dirname(save_path)
            os.makedirs(save_dir, exist_ok=True)

    def evaluate(self, problem: Problem, objectives: Objectives) -> Any:
        pyplot.legend()

        if self.save_path:
            pyplot.savefig(self.save_path)

        if self.show:
            pyplot.show()

        pyplot.clf()


class Time(Indicator):
    def __init__(self):
        super().__init__()
        self.start = time.time()

    def evaluate(self, problem: Problem, objectives: Objectives) -> Any:
        stop = time.time()
        time_delta = stop - self.start
        return time_delta


class IterationTime(Indicator):
    def __init__(self):
        super().__init__()
        self.start = time.time()

    def evaluate(self, problem: Problem, objectives: Objectives) -> Any:
        stop = time.time()
        time_delta = stop - self.start
        self.start = stop
        return time_delta


def worse(objectives: Objectives) -> Vector:
    worse_objective = tuple(max(objective_values) for objective_values in zip(*objectives))  # type: Tuple[float]
    return worse_objective
