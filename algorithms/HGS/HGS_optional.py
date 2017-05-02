from algorithms.base import drivertools
import numpy as np

# utility methods for RHS that are currently either not working or not necessary,
# but the author need a method of glancing at them very quickly


def population_from_delegate_mutate(delegate, size, dims, rate, eta):
    population = [[x for x in delegate]]
    for _ in range(size - 1):
        population.append(drivertools.mutate(delegate, dims, rate, eta))
    return population


def redundant_projection(pop_a, pop_b, variances_multiplier):
    if pop_a is pop_b:
        return False

    mean_pop_a = np.mean(pop_a, axis=0)
    mean_pop_b = np.mean(pop_b, axis=0)

    diff_vector = mean_pop_b - mean_pop_a
    len_diff_vector = np.linalg.norm(diff_vector)
    diff_vector /= len_diff_vector

    projections_a = [np.dot((x - mean_pop_a), diff_vector) for x in pop_a]
    projections_std_a = np.std(projections_a)
    projections_b = [np.dot((x - mean_pop_b), diff_vector) for x in pop_b]
    projections_std_b = np.std(projections_b)

    return (variances_multiplier * projections_std_a + variances_multiplier * projections_std_b) > len_diff_vector


def redundant_lda(pop_a, pop_b, variances_multiplier=2.0):
    if pop_a is pop_b:
        return False

    combined = [x for x in pop_a]
    combined_class = [0 for _ in pop_a]
    for x in pop_b:
        combined.append(x)
        combined_class.append(1)

    lda_instance = lda.LDA(n_components=1)
    lda_projection = None
    while lda_projection is None:
        try:
            lda_projection = [x[0] for x in lda_instance.fit_transform(combined, combined_class)]
        except ValueError:
            # print("??? intelowy error!")
            # print(pop_a)
            # print(pop_b)
            # print("intelowy error! ???")
            return False

    projection_a = [x for i, x in enumerate(lda_projection) if combined_class[i] == 0]
    projection_b = [x for i, x in enumerate(lda_projection) if combined_class[i] == 1]

    mean_a = np.mean(projection_a)
    mean_b = np.mean(projection_b)

    std_a = np.std(projection_a)
    std_b = np.std(projection_b)

    return (variances_multiplier * (std_a + std_b)) > math.fabs(mean_a - mean_b)


def compare_centers(pop_a, pop_b, variances_multiplier=2.0):
    mean_pop_a = np.mean(pop_a, axis=0)
    mean_pop_b = np.mean(pop_b, axis=0)

    diff_vector = mean_pop_b - mean_pop_a
    len_diff_vector = np.linalg.norm(diff_vector)
    diff_vector /= len_diff_vector

    projections_a = [np.dot((x - mean_pop_a), diff_vector) for x in pop_a]
    projections_std_a = np.std(projections_a)
    projections_b = [np.dot((x - mean_pop_b), diff_vector) for x in pop_b]
    projections_std_b = np.std(projections_b)

    # noinspection PyTypeChecker
    return (variances_multiplier * projections_std_a + variances_multiplier * projections_std_b) > len_diff_vector


def scaled_domain(dims, eta):
    return [(0, (b - a) / eta) for a, b in dims]


def code(xs, eta, dims):
    return [eta * x + a for x, (a, b) in zip(xs, dims)]


def code_all(vectors, eta, dims):
    return [code(xs, eta, dims) for xs in vectors]


def decode(xs, eta, dims):
    return [(x - a) / eta for x, (a, b) in zip(xs, dims)]


def decode_all(vectors, eta, dims):
    return [decode(xs, eta, dims) for xs in vectors]


def scale(xs, eta_from, eta_to):
    return [(eta_from / eta_to) * x for x in xs]


def scale_all(vectors, eta_from, eta_to):
    return [scale(xs, eta_from, eta_to) for xs in vectors]