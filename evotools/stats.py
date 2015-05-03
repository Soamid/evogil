import random

def sample_wr(population, k):
    """Chooses k random elements (with replacement) from a population"""
    n = len(population) - 1
    return [population[int(random.randint(0, n))] for i in range(k)]


def average(xs):
    if len(xs) == 0:
        return -float("inf")
    return sum(xs) * 1.0 / len(xs)


def bootstrap(population, f, n, k, alpha):
    btstrp = sorted(f(sample_wr(population, k)) for i in range(n))
    return {
        "confidence": 100.0 * (1 - 2 * alpha),
        "from": btstrp[int(1.0 * n * alpha)],
        "to": btstrp[int(1.0 * n * (1 - alpha))],
        "metrics": f(population)
    }
