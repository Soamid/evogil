from ep.utils import ea_utils as utils
from ep.utils.driver import Driver
from problems.coemoa_a import problem


class OMOPSO(Driver):
    ETA = 0.0075

    def __init__(self, population, fitnesses, dims):
        super().__init__(population, dims, fitnesses, 0, 0)
        self.population = population
        self.leaders_size = len(population)  # parameter?
        self.archive = Archive(self.ETA)
        self.leader_archive = LeaderArchive(self.leaders_size)

        self.calculate_objectives(self.__population)
        self.init_leaders()
        self.personal_bests = list(self.__population)


    def init_leaders(self):
        for p in self.__population:
            self.leader_archive.add(p)

        self.leader_archive.trim()

        for p in self.leader_archive:
            self.archive.add(p)


    def steps(self, condI, budget=None):
        cost = 0

        for _ in condI:
            if budget is not None and cost > budget:
                break

        return cost

    def calculate_objectives(self, pop):
        for p in pop:
            p.objectives = [o(p.value)
                            for o in self.fitnesses]


    @property
    def population(self):
        return [x.value for x in self.__population]

    @population.setter
    def population(self, pop):
        self.__population = [Individual(x) for x in pop]

    def finish(self):
        return [x.value for x in self.archive]


class Individual:
    def __init__(self, value):
        self.value = value
        self.speed = 0
        self.crowd_val = 0
        self.objectives = []
        self.fitness = 0


    def dominates(self, p2, eta=0):
        at_least_one = False
        for i in range(0, len(self.objectives)):
            if p2.objectives[i] / (1 + eta) < self.objectives[i]:
                return False
            elif p2.objectives[i] / (1 + eta) > self.objectives[i]:
                at_least_one = True

        return at_least_one

    def equal_obj(self, p):
        for i in range(len(self.objectives)):
            if self.objectives[i] != p.objectives[i]:
                return False
        return True


class Archive(object):
    def __init__(self, eta=0.0):
        self.archive = []
        self.eta = eta

    def __iter__(self):
        return self.archive.__iter__()

    def add(self, p):
        new_archive = []

        for l in self.archive:
            if l.dominates(p, self.eta):
                return False
            elif not p.dominates(l, self.eta):
                new_archive.append(l)
            elif l.equal_obj(p):
                return False

        self.archive = new_archive
        self.archive.append(p)


class LeaderArchive(Archive):
    def __init__(self, size):
        super().__init__()
        self.size = size

    def trim(self):
        if len(self.archive) > self.size:
            self.crowding()
            self.archive.sort(key=lambda x: x.crowd_val, reverse=True)
            self.archive = self.archive[:self.size]

    def crowding(self):
        for p in self.archive:
            p.crowd_val = 0

        obj_n = len(self.archive[0].objectives)

        archive_len = len(self.archive)
        for i in range(obj_n):
            self.archive.sort(key=lambda x: x.objectives[i])
            obj_min = self.archive[0].objectives[i]
            obj_max = self.archive[archive_len - 1].objectives[i]

            self.archive[0].crowd_val = float('inf')
            self.archive[archive_len - 1].crowd_val = float('inf')

            for j in range(1, archive_len - 1):
                dist = self.archive[j].objectives[i] - self.archive[j - 1].objectives[i]
                dist /= (obj_max - obj_min)
                self.archive[j].crowd_val += dist


if __name__ == '__main__':
    algo = OMOPSO(utils.gen_population(80, problem.dims), problem.fitnesses, problem.dims)
    print(algo.population)
    print(algo.finish())
