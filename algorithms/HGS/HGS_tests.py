import matplotlib.pyplot as plt

from algorithms.HGS.HGS import *
from algorithms.HGS.HGS_optional import *


# def __redundant_test():
#     sample_pop_a = [
#         [random.gauss(0.3, 0.015), random.gauss(0.3, 0.05)] for _ in range(1000)
#     ]
#     sample_pop_b = [
#         [random.gauss(0.5, 0.04), random.gauss(0.5, 0.025)] for _ in range(1000)
#     ]
#
#     lda_instance = lda.LDA(n_components=1)
#
#     combined = [x for x in sample_pop_a]
#     combined_class = [0 for _ in sample_pop_a]
#     for x in sample_pop_b:
#         combined.append(x)
#         combined_class.append(1)
#     post_lda = lda_instance.fit_transform(combined, combined_class)
#
#     projection_a = [x for i, x in enumerate(post_lda) if combined_class[i] == 0]
#     projection_b = [x for i, x in enumerate(post_lda) if combined_class[i] == 1]
#
#     plt.scatter(projection_a, [0.5 for _ in projection_a], c="b")
#     plt.scatter(projection_b, [0.5 for _ in projection_b], c="r")
#
#     mean_a = np.mean(projection_a)
#     mean_b = np.mean(projection_b)
#
#     plt.scatter([mean_a], [0.5], c="y")
#     plt.scatter([mean_b], [0.5], c="y")
#
#     std_a = np.std(projection_a)
#     std_b = np.std(projection_b)
#
#     plt.scatter([mean_a + 2 * std_a, mean_a - 2 * std_a], [0.5, 0.5], c="m")
#     plt.scatter([mean_b + 2 * std_b, mean_b - 2 * std_b], [0.5, 0.5], c="c")
#
#     plt.show()


def __compare_test():
    sample_pop_a = [
        [random.gauss(0.3, 0.015), random.gauss(0.3, 0.05)] for _ in range(1000)
    ]
    # plt.scatter([x[0] for x in sample_pop_a], [x[1] for x in sample_pop_a], c='b')

    mean_pop_a = np.mean(sample_pop_a, axis=0)
    plt.scatter([mean_pop_a[0]], [mean_pop_a[1]], c="g")
    plt.scatter([mean_pop_a[0] + 2 * 0.015], [mean_pop_a[1]], c="g")
    plt.scatter([mean_pop_a[0] - 2 * 0.015], [mean_pop_a[1]], c="g")
    plt.scatter([mean_pop_a[0]], [mean_pop_a[1] + 2 * 0.05], c="g")
    plt.scatter([mean_pop_a[0]], [mean_pop_a[1] - 2 * 0.05], c="g")

    sample_pop_b = [
        [random.gauss(0.5, 0.04), random.gauss(0.5, 0.025)] for _ in range(1000)
    ]
    # plt.scatter([x[0] for x in sample_pop_b], [x[1] for x in sample_pop_b], c='r')

    mean_pop_b = np.mean(sample_pop_b, axis=0)
    plt.scatter([mean_pop_b[0]], [mean_pop_b[1]], c="g")
    plt.scatter([mean_pop_b[0] + 2 * 0.04], [mean_pop_b[1]], c="g")
    plt.scatter([mean_pop_b[0] - 2 * 0.04], [mean_pop_b[1]], c="g")
    plt.scatter([mean_pop_b[0]], [mean_pop_b[1] + 2 * 0.025], c="g")
    plt.scatter([mean_pop_b[0]], [mean_pop_b[1] - 2 * 0.025], c="g")

    diff_vector = mean_pop_b - mean_pop_a
    print(diff_vector)
    ax = plt.axes()
    # ax.arrow(mean_pop_a[0], mean_pop_a[1], diff_vector[0],diff_vector[1], head_width=0.0, head_length=0.0, fc='r', ec='r')

    len_diff_vector = np.linalg.norm(diff_vector)
    diff_vector /= len_diff_vector
    print(diff_vector)
    print(diff_vector[0] ** 2 + diff_vector[1] ** 2)

    dots_a = [np.dot((x - mean_pop_a), diff_vector) for x in sample_pop_a]
    flatted_a = [d * diff_vector + mean_pop_a for d in dots_a]
    # print(dots_a)
    # plt.scatter([x[0] for x in flatted_a], [x[1] for x in flatted_a], c='k')

    # for i, x in enumerate(sample_pop_a):
    # arr = flatted_a[i] - x
    # ax.arrow(x[0], x[1], arr[0], arr[1], head_width=0.0, head_length=0.0, fc='y', ec='y')

    dots_std_a = np.std(dots_a)
    print(dots_std_a)

    var_a = mean_pop_a + (2 * dots_std_a * diff_vector)
    plt.scatter([var_a[0]], [var_a[1]], c="c")

    dots_b = [np.dot((x - mean_pop_b), diff_vector) for x in sample_pop_b]
    flatted_b = [d * diff_vector + mean_pop_b for d in dots_b]
    # print(dots_b)
    # plt.scatter([x[0] for x in flatted_b], [x[1] for x in flatted_b], c='k')

    dots_std_b = np.std(dots_b)
    print(dots_std_b)

    var_b = mean_pop_b + (-2 * dots_std_b * diff_vector)
    plt.scatter([var_b[0]], [var_b[1]], c="m")

    print(len_diff_vector)
    print(2 * dots_std_a + 2 * dots_std_b)
    effect = (2 * dots_std_a + 2 * dots_std_b) > len_diff_vector
    print(effect)

    # plt.xlim([0.0, 1.0])
    # plt.ylim([0.0, 1.0])
    plt.grid(True)
    plt.axes().set_aspect("equal", "datalim")
    plt.show()


def __coding_test():
    sample_dims = [(0.0, 1.0), (0.0, 1.0), (0.0, 1.0)]
    eta_0 = 4096.0
    eta_1 = 128.0
    eta_2 = 1.0
    print(scaled_domain(sample_dims, eta_0))
    print(scaled_domain(sample_dims, eta_1))
    print(scaled_domain(sample_dims, eta_2))

    points = [[random.uniform(a, b) for a, b in sample_dims] for _ in range(1)]
    print(points)
    decoded = decode_all(points, eta_0, sample_dims)
    print(decoded)
    coded = code_all(decoded, eta_0, sample_dims)
    print(coded)
    a = 13.45123412341234123412341234
    print(a)
    a /= 10 ** 25
    print(a)
    a *= 10 ** 25
    print(a)