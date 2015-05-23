class DriverGen:
    def __init__(self,
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

    def population_generator(self):
        """ Generator.
        Yiels proxies, allowing them to be modified and to come back (via generator.send())
        to perform migration.

        Each proxy satisfies the following interface:
            proxy.cost
            proxy.finalized_population()
            proxy.get_immigrants()
            proxy.send_emigrants()

        The emigration is actually performed on the driver ONLY IF the proxy with .send_emigrants() called
        is sent back to this generator.

        See: https://gist.github.com/kgadek/e018008be8cfcce313fd
        """
        raise NotImplementedError

    class Proxy:
        def __init__(self, cost):
            self.cost = cost

        def finalized_population(self):
            """
            :return: Returns finalized population
            """
            raise NotImplementedError

        def get_immigrants(self):
            """
            :return: Returns individuals selected from the population.
            """
            raise NotImplementedError

        def send_emigrants(self, emigrants):
            """
            :param emigrants: Individuals that shall be assimilated into the population.
            :return: Does not return. This Proxy object shall be passed back to the generator.
            """
            raise NotImplementedError
