# coding=utf-8
import random
import math
import algorithms.utils.driver


class SGA(algorithms.utils.driver.Driver):

    class Tournament:
        def __init__(self, compare_key):
            self.tournament_size = 2
            self.compare_key = compare_key

        def __call__(self, pool: '[([Float], [Float])]') -> '([Float], [Float])':
            sub_pool = random.sample(pool, self.tournament_size)
            return min(sub_pool, key=self.compare_key)

    def _compare_key(self, x_f: '([Float], [Float])') -> 'comparable':
        x, fx = x_f
        return sum(fx)

    @property
    def compare_key(self) -> '([Float], [Float]) -> comparable':
        return self._compare_key

    @compare_key.setter
    def compare_key(self, cmp_k: '([Float], [Float]) -> comparable'):
        self._compare_key = cmp_k
        # The reason for creating @property: synchronize value with that of self.select
        if hasattr(self.select, 'compare_key'):
            self.select.compare_key = cmp_k

    def crossover(self, inds: '[([Float], [Float])]') -> '([Float], [Float])':
        def coin() -> 'Bool':
            return random.random() < self.mutation_probability

        [x, y] = inds
        return [xx_f if coin() else yy_f
                for xx_f, yy_f in zip(x, y)]

    class Mutation:
        def __init__(self):
            self.mutation_probability = 0.5
            self.sigma = 0.2

        def __call__(self, x_f: '([Float], [Float])') -> '[Float]':
            def coin():
                return random.random() < self.mutation_probability

            x, fx = x_f
            return [random.gauss(xx, self.sigma) if coin() else xx
                    for xx in x]

    def are_similar(self, xs: '[Float]', ys: '[Float]', sigmas: '[Float]') -> 'Bool':
        return all(abs(x - y) < sigma/2 for x, y, sigma in zip(xs, ys, sigmas))

    def __init__(self,
                 population,
                 dims,
                 fitnesses,
                 mutation_variance,
                 crossover_variance):
        super().__init__(dims=dims,
                         fitnesses=fitnesses,
                         mutation_variance=mutation_variance,
                         crossover_variance=crossover_variance,
                         population=None)
        self.fitnesses = fitnesses
        self.population = population  # side-effect: calculating fitnesses
        self.select = SGA.Tournament(self._compare_key)
        self.mutate = SGA.Mutation()

    @property
    def population(self) -> '[[Float]]':
        return [x for x, fx in sorted(self._population, key=self._compare_key)]

    @population.setter
    def population(self, pop: '[[Float]]'):
        self._population = [(x, self._calc_fitnesses(x)) for x in pop]

    def get_indivs_inorder(self):
        return self.population

    def contains_similar(self, indiv: '[Float]', sigmas: '[Float]') -> 'Bool':
        return any(self.are_similar(indiv, x, sigmas) for x, fx in self._population)

    def steps(self):
        while True:
            self.population = [self.mutate(self.crossover([self.select(self._population),
                                                           self.select(self._population)]))
                               for _ in self._population]
            cost = 100
            yield cost, self.population


    def _calc_fitnesses(self, x):
        return [f(x) for f in self.fitnesses]

    def current_result_scalar(self):
        l_pop = len(self._population)
        if l_pop == 0:
            return 0
        return sum(1.0*sum(math.fabs(ffx) for ffx in fx) / len(fx) for x, fx in self._population) / len(self._population)
