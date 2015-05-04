########################################################################################################################
#
#
#  ______     ________   _______    _______      ________     ______        _        _________   ________   ______
# |_   _ `.  |_   __  | |_   __ \  |_   __ \    |_   __  |  .' ___  |      / \      |  _   _  | |_   __  | |_   _ `.
#   | | `. \   | |_ \_|   | |__) |   | |__) |     | |_ \_| / .'   \_|     / _ \     |_/ | | \_|   | |_ \_|   | | `. \
#   | |  | |   |  _| _    |  ___/    |  __ /      |  _| _  | |           / ___ \        | |       |  _| _    | |  | |
#  _| |_.' /  _| |__/ |  _| |_      _| |  \ \_   _| |__/ | \ `.___.'\  _/ /   \ \_     _| |_     _| |__/ |  _| |_.' /
# |______.'  |________| |_____|    |____| |___| |________|  `.____ .' |____| |____|   |_____|   |________| |______.'
#
#
#
# Nie, serio.
#
# Cokolwiek zmieniacie, zmieniajcie od razu w problems/**/run.py .
#
#
#
#
########################################################################################################################
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#

"""
.. module:: test_spea2
    :platform: Unix, Windows
    :synopsis: Strength Pareto Evolutionary Algorithm
    :author: Michal Idzik <idzik@student.agh.edu.pl>
"""
import time
import pylab


from benchmarks import emoa_c, parabol, kursawe, emoa_a, emoa_b, emoa_d, emoa_e
from algorithms.utils import ea_utils as utils
from algorithms.SPEA2.SPEA2 import SPEA2


def save_plot(fitnesses, population, name, analytical, time):
    print("   Finished for benchmark " + name)
    X = [fitnesses[0](x) for x in population]
    Y = [fitnesses[1](x) for x in population]
    fig = pylab.figure()
    pylab.plot()
    pylab.xlabel("funkcja celu I")
    pylab.ylabel("funkcja celu II")
    pylab.figtext(.50, .95, "czas wykonywania: " + str(time) + " s", horizontalalignment='center', verticalalignment='center')
    pylab.scatter(X,Y, c='b')
    pylab.scatter(analytical[0], analytical[1], c='r')
    fig.savefig('../../docs/figures/' + name + '.png')
    # pylab.show()

benchmarks = [emoa_e]

for fitnesses, dims, name, anal in benchmarks:
    archive_size = 100
    initial_population = utils.gen_population(80, dims)
    algo = SPEA2(initial_population, fitnesses, dims,[1], [1])
    start = time.clock()
    cost = algo.steps(utils.condition_count(20))
    elapsed = (time.clock() - start)
    save_plot(fitnesses, algo.population, name,anal, elapsed)
    print('cost: ' + str(cost))








