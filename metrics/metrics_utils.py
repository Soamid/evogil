import logging
import math

import numpy as np

from evotools.ea_utils import dominates

EPSILON = np.finfo(float).eps


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


def generational_distance(solution, pareto):
    return distance(solution, pareto)


def inverse_generational_distance(solution, pareto):
    return distance(pareto, solution)


def non_domination_ratio(solution, not_dominated_solution):
    return float(len(not_dominated_solution)) / float(len(solution))


def spacing(solution):
    dims = len(solution[0])

    min_distances = []
    for i, ind_a in enumerate(solution):
        distances = []
        for j, ind_b in enumerate(solution):
            if not i == j:
                dist = sum([math.fabs(ind_a[k] - ind_b[k]) for k in range(dims)])
                distances.append(dist)
        if len(distances) > 0:
            min_distances.append(min(distances))

    if len(min_distances) > 0:
        mean_dist = np.mean(min_distances)
    else:
        mean_dist = 0
    dist_sum = sum([(mean_dist - dist) ** 2 for dist in min_distances])
    return math.sqrt(dist_sum / (float(len(solution) - 1) + EPSILON))


def distance(from_set, to_set):
    distances = [
        min([euclid_sqr_distance(f, t) for t in to_set])
        for f in from_set
    ]
    return math.sqrt(sum(distances) / len(distances))

def pareto_dominance_indicator(solution, not_dominated_solution, all_solutions):
    non_dominated_intersection = [s for s in not_dominated_solution if tuple(s) in all_solutions]
    return len(non_dominated_intersection) / len(all_solutions)

def filter_not_dominated2(ind_set):
    d = {tuple(ind) : [not dominates(other_ind, ind) for other_ind in ind_set] for ind in ind_set}
    result= [ind for ind in d.keys() if all(d[ind])]
    # for x in result:
    #     for y in result:
    #         if dominates(x,y) or dominates(y,x):
    #             print("co do chuja wacława?!")
    return result


def filter_not_dominated(ind_set):
    not_dominated = []
    for ind in ind_set:
        dominated_by_sth = False
        new_not_dominated = []
        for nd_ind in not_dominated:
            if not dominates(ind, nd_ind):
                new_not_dominated.append(nd_ind)
            if dominates(nd_ind, ind):
                dominated_by_sth = True
        if not dominated_by_sth:
            new_not_dominated.append(ind)
        not_dominated = new_not_dominated
    return not_dominated




