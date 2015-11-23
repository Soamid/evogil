import algorithms.base.hv as hv
import evotools.epsilon as eps
import evotools.metrics_utils as metrics_utils

EPSILON = eps.Epsilon()


# do wyfiltrowania niezdominowanej czesci populacji
def filter_not_dominated(solution):
    return metrics_utils.filter_not_dominated(solution)


#
# METRYKI
#

# im mniejszy tym lepszy, jak daleko solution od pareto, zbieznosc
def generational_distance(solution, not_dominated_solution, pareto):
    return metrics_utils.generational_distance(not_dominated_solution, pareto)


# im mniejszy tym lepszy, jak daleko pareto od solution, zbieznosc + pokrycie calosci
def inverse_generational_distance(solution, not_dominated_solution, pareto):
    return metrics_utils.inverse_generational_distance(solution, pareto)


# im mniejszy tym lepszy, gorsza z wartosci : GD, IGD dla danego rozwiazania
def average_hausdorff_distance(solution, not_dominated_solution, pareto):
    return max(generational_distance(solution, not_dominated_solution, pareto),
               inverse_generational_distance(solution, not_dominated_solution, pareto))


# im wiekszy tym lepszy, smieszna forma odleglosci, ostra zbieznosc
def epsilon(solution, not_dominated_solution, pareto):
    return EPSILON.epsilon(not_dominated_solution, pareto)


# im wiekszy tym lepszy, jak szeroka przestrzen pokryta, zakres dostarczanych opcji
def extent(solution, not_dominated_solution, pareto):
    return metrics_utils.extent(solution)


# im mniejszy tym lepszy, jak rowne sa odleglosci miedzy elementami populacji, jakosc pokrycia
def spacing(solution, not_dominated_solution, pareto):
    return metrics_utils.spacing(not_dominated_solution)


# im wiekszy tym lepszy, jak duzo rozwiazan jest w niezdominowanej czesci, jakosc rozwiazania
def non_domination_ratio(solution, not_dominated_solution, pareto):
    return metrics_utils.non_domination_ratio(solution, not_dominated_solution)


# im wiekszy tym lepszy, jak duzy hipervolume zdominowany, zbieznosc i pokrycie
def hypervolume(solution, not_dominated_solution, pareto):
    dims = len(pareto[0])
    reference_point = [50.0 for _ in range(dims)]
    # TODO kij wie jaki powinien byc -.-
    hv_instance = hv.HyperVolume(reference_point)
    return hv_instance.compute(not_dominated_solution)

# im wiekszy tym lepszy, jaka czesc niezdominowanych ze wszystkich metod stanowia niezdominowane z podanego rozwiazania
def pareto_dominance_indicator(solution, not_dominated_solution, all_solutions):
    return metrics_utils.pareto_dominance_indicator(solution, not_dominated_solution, all_solutions)


if __name__ == '__main__':
    # my_pareto = [[0., 1., 1.], [1., 0., 1.], [1., 1., 0.]]
    # my_solution = [[4.3, 1.5, 1.3], [13.0, 1.5, 1.37], [0.34, 14.5, 14.3], [1.3, 11.5, 6.3]]
    my_pareto = [[1, 5], [5, 1],
                 # [2,2]
                 ]
    my_solution = [[2, 6], [6, 2],
                   # [3,3]
                   # [6,6]
                   ]
    my_other_solution = [[3, 3],[6, 6]]
    my_not_dominated_solution = filter_not_dominated(my_solution)
    print(my_not_dominated_solution)

    print(generational_distance(my_solution, my_not_dominated_solution, my_pareto))
    print(inverse_generational_distance(my_solution, my_not_dominated_solution, my_pareto))
    print(average_hausdorff_distance(my_solution, my_not_dominated_solution, my_pareto))
    print(epsilon(my_solution, my_not_dominated_solution, my_pareto))
    print(extent(my_solution, my_not_dominated_solution, my_pareto))
    print(spacing(my_solution, my_not_dominated_solution, my_pareto))
    print(non_domination_ratio(my_solution, my_not_dominated_solution, my_pareto))
    print(hypervolume(my_solution, my_not_dominated_solution, my_pareto))
    print(pareto_dominance_indicator(my_solution, my_not_dominated_solution, [my_solution, my_other_solution]))
