from pprint import pprint

from algorithms.FVMOEA.algorithm import FVMOEA
from algorithms.FVMOEA.crossover import SBXCrossover
from algorithms.FVMOEA.indicators import *
from algorithms.FVMOEA.initialization import UniformInitialization
from algorithms.FVMOEA.mutation import PolynomialMutation
from algorithms.FVMOEA.problem import *
from algorithms.FVMOEA.selection import BinaryTournament2


def main():
    variables_count = 3
    population_size = 150

    problem = UF1(variables_count=variables_count)
    problem_name = problem.__class__.__name__

    algorithm = FVMOEA(
        problem=problem,

        indicators=[
            IterationTime(),
            Time(),

            GD(plot=True),
            IGD(plot=True),
            Spread(plot=True),
            Epsilon(plot=True),
            Plot(show=False, save_path=f'plots/{problem_name}/indicators.png'),

            HyperVolume(plot=True),
            Plot(show=False, save_path=f'plots/{problem_name}/hypervolume.png'),

            Pareto(),
            Plot(show=False, save_path=f'plots/{problem_name}/pareto.png')
        ],

        initialization=UniformInitialization(),

        selection=BinaryTournament2(),

        crossover=SBXCrossover(
            probability=0.9,
            distribution_index=20.0
        ),

        mutation=PolynomialMutation(
            probability=1.0 / variables_count,
            distribution_index=20.0
        ),

        batch_size=int(0.2 * population_size),
        population_size=population_size,
        maximum_function_evaluations=10000,
    )

    result = algorithm.run()
    print('Solution:')
    pprint(result)


if __name__ == '__main__':
    main()
