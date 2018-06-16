import random

from algorithms.base.drivergen import ImgaProxy, Driver
from evotools.ea_utils import dominates


class Individual:
    def __init__(self, vector, fitnesses):
        self.v = vector
        self.fit = [f(self.v) for f in fitnesses]


class BOGOImgaProxy(ImgaProxy):
    def __init__(self, driver, cost, archive):
        super().__init__(driver, cost)
        self.archive = archive

    def finalized_population(self):
        return [x.v for x in self.archive]

    def current_population(self):
        return [x.v for x in self.archive]

    def deport_emigrants(self, immigrants):
        pass

    def assimilate_immigrants(self, emigrants):
        pass


class BOGO(Driver):
    def __init__(self,
                 population,
                 dims,
                 fitnesses,
                 mutation_variance,
                 crossover_variance):
        self.archive = []
        self.fitnesses = fitnesses
        self.dims = dims
        self.cost = 0
        for p in population:
            self.cost += 1
            ind = Individual(p, self.fitnesses)
            self.refresh_archive(ind)
        self.finished = False

    def refresh_archive(self, individual):
        new_archive = []
        individual_dominated = False
        for archival in self.archive:
            if not individual_dominated and dominates(archival.fit, individual.fit):
                individual_dominated = True
            elif not dominates(individual.fit, archival.fit):
                new_archive.append(archival)
        if not individual_dominated:
            new_archive.append(individual)
        self.archive = new_archive

    def finalized_population(self):
        return [x.v for x in self.archive]

    def step(self):
        self.next_step()
        print("cost", self.cost, "archive", len(self.archive))
        return self.emit_next_proxy()

    def next_step(self):
        vector = [random.uniform(a, b) for (a, b) in self.dims]
        self.cost += 1
        ind = Individual(vector, self.fitnesses)
        self.refresh_archive(ind)
