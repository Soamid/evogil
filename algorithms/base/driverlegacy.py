# coding=utf-8


class DriverLegacy:

    # noinspection PyUnusedLocal
    def __init__(self,
                 population,  # this is only to enforce the sole existence of such parameter ;)
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

    @property
    def population(self):
        """ :return: Zwraca bieżącą populację. """
        raise NotImplementedError

    def finish(self):
        """ :return: Zwraca rezultat (ostateczną populację). """
        raise NotImplementedError

    def steps(self, _iterator: 'Iterator _'):
        """ Wykonuje kroki algorytmu aż iterator przestanie zwracać wartości
        :param _iterator: dowolny iterator.
        :return: Kosz działania liczony w ilości wywołanych funkcji fitness.
        """
        raise NotImplementedError

