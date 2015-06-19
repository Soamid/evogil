import ep.utils.ea_utils as ea_utils
import ep.utils.epsilon as eps
import ep.smsemoa.hv as hv

EPSILON = eps.Epsilon()


# do wyfiltrowania niezdominowanej czesci populacji
def filter_not_dominated(solution):
    pass
filter_not_dominated = ea_utils.filter_not_dominated


#
# METRYKI
#


# im mniejszy tym lepszy, jak daleko solution od pareto, zbieznosc
def generational_distance(solution, not_dominated_solution, pareto):
    return ea_utils.generational_distance(not_dominated_solution, pareto)


#im mniejszy tym lepszy, jak daleko pareto od solution, zbieznosc + pokrycie calosci
def inverse_generational_distance(solution, not_dominated_solution, pareto):
    return ea_utils.inverse_generational_distance(solution, pareto)


#im wiekszy tym lepszy, smieszna forma odleglosci, ostra zbieznosc
def epsilon(solution, not_dominated_solution, pareto):
    return EPSILON.epsilon(not_dominated_solution, pareto)


#im wiekszy tym lepszy, jak szeroka przestrzen pokryta, zakres dostarczanych opcji
def extent(solution, not_dominated_solution, pareto):
    return ea_utils.extent(solution)


#im mniejszy tym lepszy, jak rowne sa odleglosci miedzy elementami populacji, jakosc pokrycia
def spacing(solution, not_dominated_solution, pareto):
    return ea_utils.spacing(not_dominated_solution)


#im wiekszy tym lepszy, jak duzo rozwiazan jest w niezdominowanej czesci, jakosc rozwiazania
def non_domination_ratio(solution, not_dominated_solution, pareto):
    return ea_utils.non_domination_ratio(solution, not_dominated_solution)


#im wiekszy tym lepszy, jak duzy hipervolume zdominowany, zbieznosc i pokrycie
def hypervolume(solution, not_dominated_solution, pareto):
    dims = len(pareto[0])
    reference_point = [100.0 for _ in range(dims)]
    #TODO kij wie jaki powinien byc -.-
    hv_instance = hv.HyperVolume(reference_point)
    return hv_instance.compute(not_dominated_solution)


if __name__ == '__main__':
    pareto = [[0., 1., 1.], [1., 0., 1.], [1., 1., 0.]]
    solution = [[4.3, 1.5, 1.3], [13.0, 1.5, 1.37], [0.34, 14.5, 14.3], [1.3, 11.5, 6.3]]
    not_dominated_solution = filter_not_dominated(solution)
    print(not_dominated_solution)

    print(generational_distance(solution, not_dominated_solution, pareto))
    print(inverse_generational_distance(solution, not_dominated_solution, pareto))
    print(epsilon(solution, not_dominated_solution, pareto))
    print(extent(solution, not_dominated_solution, pareto))
    print(spacing(solution, not_dominated_solution, pareto))
    print(non_domination_ratio(solution, not_dominated_solution, pareto))
    print(hypervolume(solution, not_dominated_solution, pareto))


