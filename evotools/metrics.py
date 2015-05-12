import itertools
import math

def distance_from_pareto(solution, pareto):
    return sum([min([euclid_distance(x, y)
                     for y in pareto])
                for x in solution]) / len(solution)


def distribution(solution, sigma):
    solutionL = list(solution)
    return sum(sum( 1
                    for y in solutionL
                    if euclid_distance(x, y) > sigma
                   ) / (len(solutionL) - 1)
                for x in solutionL
              ) / len(solutionL)


def extent(solution):
    return math.sqrt(sum( max( math.fabs(x[i] - y[i])
                               for x, y
                               in itertools.product(solution, solution)
                              )
                          for i
                          in range( len(solution[0]) )
                        )
                    )

def euclid_distance(xs, ys):
    xs, ys = list(xs), list(ys)
    if len(xs) != len(ys) or len(xs) == 0:
        return 9999999
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(xs, ys)))

def euclid_sqr_distance(xs, ys):
    return sum((x - y) ** 2 for x, y in zip(xs, ys))
