import itertools
import math
from evotools.log_helper import get_logger
from evotools.timing import log_time, process_time

logger = get_logger(__name__)


def distance_from_pareto(solution, pareto):
    solution = list(solution)
    logger.debug("distance_from_pareto: input length %d", len(solution))
    with log_time(process_time, logger, "distance_from_pareto computation time: {time_res:.3}s"):
        return sum([min([euclid_distance(x, y)
                         for y in pareto])
                    for x in solution]) / len(solution)


def distribution(solution, sigma=0.5):
    solution = list(solution)
    logger.debug("distribution: input length %d", len(solution))
    with log_time(process_time, logger, "distribution computation time: {time_res:.3}s"):
        return sum(sum(1
                       for y in solution
                       if sigma < math.sqrt(sum((x1 - y1) ** 2 for x1, y1 in zip(x, y)))
                       )
                   for x in solution
                   ) / (len(solution) * (len(solution) - 1))


def extent(solution):
    logger.debug("extent: input length %d", len(solution))
    with log_time(process_time, logger, "extent computation time: {time_res:.3}s"):
        return math.sqrt(sum(max(math.fabs(x[i] - y[i])
                                 for x in solution
                                 for y in solution
                                 )
                             for i
                             in range(len(solution[0]))
                             )
                         )


def euclid_distance(xs, ys):
    xs, ys = list(xs), list(ys)
    if len(xs) != len(ys) or len(xs) == 0:
        return 9999999  # TODO [kgdk] 19 maj 2015: or maybe use float('inf') here ?
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(xs, ys)))


def euclid_sqr_distance(xs, ys):
    return sum((x - y) ** 2 for x, y in zip(xs, ys))

