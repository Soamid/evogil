import itertools
import logging
import math
from evotools.timing import log_time, process_time


def distance_from_pareto(solution, pareto):
    logger = logging.getLogger(__name__)
    solution = list(solution)
    logger.debug("distance_from_pareto: input length %d", len(solution))
    return sum([min([euclid_distance(x, y)
                     for y in pareto])
                for x in solution]) / len(solution)


def distribution(solution, sigma=0.5):
    logger = logging.getLogger(__name__)
    solution = list(solution)
    logger.debug("distribution: input length %d", len(solution))
    try:
        return sum(sum(1
                       for y in solution
                       if sigma < math.sqrt(sum((x1 - y1) ** 2 for x1, y1 in zip(x, y)))
                       )
                   for x in solution
                   ) / (len(solution) * (len(solution) - 1))
    except ZeroDivisionError:
        return float('inf')


def extent(solution):
    logger = logging.getLogger(__name__)
    logger.debug("extent: input length %d", len(solution))
    return math.sqrt(sum(max(math.fabs(x[i] - y[i])
                             for x in solution
                             for y in solution
                             )
                         for i
                         in range(len(solution[0]))
                         )
                     )


def euclid_distance(xs, ys):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(xs, ys)))


def euclid_sqr_distance(xs, ys):
    return sum((x - y) ** 2 for x, y in zip(xs, ys))

