# coding=utf-8
import numpy
import random
from algorithms.utils import ea_utils


class Driver:

    #noinspection PyUnusedLocal
    def __init__(self,
                 population,  # to istnieje tylko po to, by wymusić obecność `population` w parametrach ;)
                 dims,
                 fitnesses,
                 mutation_variance,
                 crossover_variance,
                 mutation_probability=0.05):
        self.fitnesses = fitnesses
        self.dims = dims
        self.mutation_variance = mutation_variance
        self.mutation_probability = mutation_probability
        self.crossover_variance = crossover_variance
        self.finished = False

    def mutate(self, xs):
        def coin():
            return random.random() < self.mutation_probability
        return [min(max(a, (random.gauss(x, sigma))), b) if coin() else x
                for x, (a, b), sigma in zip(xs, self.dims, self.mutation_variance)]

    def crossover(self, xs, ys):
        return [random.uniform(x, y)
                for x, y in zip(xs, ys)]

    #noinspection PyMethodMayBeStatic
    def crossover_triangular(self, xs, ys):
        return [random.triangular(low=min(x, y), high=max(x, y))
                for x, y in zip(xs, ys)]

    def crossover_beta(self, xs, ys):
        """ Rozkład beta - https://en.wikipedia.org/wiki/File:Beta_distribution_pdf.svg .
        Wyznacza a na podstawie zadanej wariancji.
        :warning: Wariancja v musi spełniać: v/(b-a) <= 0.25 gdzie [a,b] jest przestrzenią.
        """
        return [random.betavariate(v/(b-a), v/(b-a)) * abs(x-y) + min(x, y)
                for x, y, (a, b), v in zip(xs, ys, self.dims, self.crossover_variance)]

    @property
    def average(self) -> 'Individual':
        """ :return: Zwraca 'średniego' osobnika. """
        res = numpy.average(self.population, axis=0)
        if type(res) == numpy.float64:
            return []
        return list(res)

    @property
    def population(self) -> '[Individual]':
        """ :return: Zwraca bieżącą populację. """
        raise NotImplementedError

    def finish(self):
        """ :return: Zwraca rezultat (ostateczną populację). """
        raise NotImplementedError

    @staticmethod
    def rank(individuals: 'Iterator Individual', fitfun_res) -> 'Iterator Individual':
        """
        :param individuals: Grupa indywiduów.
        :param fitfun_res: Określa jak otrzymać wektor wyników.
        :return: Posortowane dane wejściowe od najlepszych do najgorszych.
        """
        return iter(indiv
                    for eqv_class in ea_utils.paretofront_layers(individuals, fitfun_res=fitfun_res)
                    for indiv in eqv_class)

    def steps(self, _iterator: 'Iterator _') -> 'Int':
        """ Wykonuje kroki algorytmu aż iterator przestanie zwracać wartości
        :param _iterator: dowolny iterator.
        :return: Kosz działania liczony w ilości wywołanych funkcji fitness.
        """
        raise NotImplementedError

    def get_indivs_inorder(self) -> 'Iterator Individual':
        """ :return: Bieżąca populacja posortowana od najlepszych do najgorszych. """
        def fitfun_res(ind):
            return [f(ind) for f in self.fitnesses]
        return Driver.rank(self.population, fitfun_res)
