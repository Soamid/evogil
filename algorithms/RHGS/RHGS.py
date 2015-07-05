from algorithms.base.drivergen import DriverGen


class RHGS(DriverGen):
    def __init__(self,
                 population,
                 dims,
                 fitnesses,
                 driver,
                 metaepoch_len=5,
                 levels=3,
                 population_sizes=[100, 20, 10],
                 scaling_coefficients=[4096.0, 128.0, 1.0]):
        super().__init__()

        self.driver = driver

        self.root = RHGS.Node(self,
                              0,
                              initial_population)

    class Node():
        def __init__(self,
                     owner,
                     level,
                     population):
            self.owner = owner
            self.driver = owner.driver(population=population,
                                       dims=owner.dims,
                                       fitnesses=owner.fitnesses,
                                       mutation_variance=owner.mutation_variance,
                                       crossover_variance=owner.crossover_variance)
            pass