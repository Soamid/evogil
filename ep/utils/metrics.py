import ep.utils.ea_utils as ea_utils
import ep.utils.epsilon as epsilon
import ep.smsemoa.hv as hv

EPSILON = epsilon.Epsilon()


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


#im mniejszy tym lepszy, smieszna forma odleglosci, ostra zbieznosc
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
    reference_point = [max([ind[k] for ind in pareto]) for k in range(dims)]
    #TODO reference point mozna by policzyc raz a dobrze, ale wtedy ladna struktura metryk sie psuje
    #TODO wiec trzeba by je trzymac policzone i rozpoznawac po jakims hashu z optymalnego frontu
    #TODO ale nie mam juz na to sily
    hv_instance = hv.HyperVolume(reference_point)
    return hv_instance.compute(not_dominated_solution)


