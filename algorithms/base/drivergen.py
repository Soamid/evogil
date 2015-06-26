class DriverGen:
    max_budget = None

    def __init__(self):
        self.finished = False
        self.level = -1
        pass

    def refresh_etas(self):
        import constants
        if self.level == -1:
            self.eta_crossover = constants.ETA_CROSSOVER_BASE
            self.eta_mutation = constants.ETA_MUTATION_BASE
        if self.level == 0:
            self.eta_crossover = constants.ETA_CROSSOVER_0
            self.eta_mutation = constants.ETA_MUTATION_0
        if self.level == 1:
            self.eta_crossover = constants.ETA_CROSSOVER_1
            self.eta_mutation = constants.ETA_MUTATION_1
        elif self.level == 2:
            self.eta_crossover = constants.ETA_CROSSOVER_2
            self.eta_mutation = constants.ETA_MUTATION_2

    def population_generator(self):
        """ Generator.
        Yiels proxies, allowing them to be modified and to come back (via generator.send())
        to perform migration.

        Each proxy satisfies the following interface:
            proxy.cost
            proxy.finalized_population()
            proxy.current_population()
            proxy.deport_emigrants()
            proxy.assimilate_immigrants()
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

        def current_population(self):
            """
            :return: Returns individuals selected from the current population.
            """
            raise NotImplementedError

        def deport_emigrants(self, immigrants):
            """
            :param immigrants: Individuals that shall be removed from the population.
            :return: Immigrants objects removed from the population. Objects should be equal to immigrants,
            but they may be expressed in driver-specific model form.
            """
            raise NotImplementedError

        def assimilate_immigrants(self, emigrants):
            """
            :param emigrants: Individuals that shall be assimilated into the population, expressed in driver-specific model form.
            :return: Does not return. This Proxy object shall be passed back to the generator.
            """
            raise NotImplementedError
