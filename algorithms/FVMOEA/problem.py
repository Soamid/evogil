from abc import ABC, abstractmethod, ABCMeta

from algorithms.FVMOEA.population import Individual


class Problem(ABC):
    def __init__(self, variables_count: int):
        self.variables_count = variables_count
        self.optimal_pareto = []
        self.fitnesses = []
        self.dims = []

    def evaluate(self, individual: Individual) -> None:
        individual.objectives = [
            fitness(individual.vector)
            for fitness in self.fitnesses
        ]


class UF(Problem, metaclass=ABCMeta):
    def __init__(self, variables_count: int):
        super().__init__(variables_count)

        dims, fitnesses, pareto_front = self.import_problem()
        self.optimal_pareto = pareto_front
        self.fitnesses = fitnesses
        self.dims = dims

    @abstractmethod
    def import_problem(self):
        pass


class UF1(UF):
    def import_problem(self):
        from problems.UF1.problem import fitnesses, dims, pareto_front
        return dims, fitnesses, pareto_front


class UF2(UF):
    def import_problem(self):
        from problems.UF2.problem import fitnesses, dims, pareto_front
        return dims, fitnesses, pareto_front


class UF3(UF):
    def import_problem(self):
        from problems.UF3.problem import fitnesses, dims, pareto_front
        return dims, fitnesses, pareto_front


class ZDT(Problem, metaclass=ABCMeta):
    def __init__(self, variables_count: int):
        super().__init__(variables_count)

        emoa_fitnesses, emoa_analytical, f1, h, g, letter = self.import_problem()

        self.fitnesses, self.dims, _, pareto_front = \
            emoa_fitnesses(f1, g, h, variables_count, letter, emoa_analytical)

        self.optimal_pareto = list(zip(*pareto_front))

    @abstractmethod
    def import_problem(self):
        pass


class ZDT1(ZDT):
    def import_problem(self):
        from problems.ZDT1.problem import emoa_fitnesses, emoa_a_analytical, f1a, ha, ga
        return emoa_fitnesses, emoa_a_analytical, f1a, ha, ga, 'a'


class ZDT2(ZDT):
    def import_problem(self):
        from problems.ZDT2.problem import emoa_fitnesses, emoa_b_analytical, f1b, hb, gb
        return emoa_fitnesses, emoa_b_analytical, f1b, hb, gb, 'b'


class ZDT3(ZDT):
    def import_problem(self):
        from problems.ZDT3.problem import emoa_fitnesses, emoa_c_analytical, f1c, hc, gc
        return emoa_fitnesses, emoa_c_analytical, f1c, hc, gc, 'c'


class ZDT4(ZDT):
    def import_problem(self):
        from problems.ZDT4.problem import emoa_fitnesses, emoa_d_analytical, f1d, hd, gd
        return emoa_fitnesses, emoa_d_analytical, f1d, hd, gd, 'd'


class ZDT6(ZDT):
    def import_problem(self):
        from problems.ZDT6.problem import emoa_fitnesses, emoa_e_analytical, f1e, he, ge
        return emoa_fitnesses, emoa_e_analytical, f1e, he, ge, 'e'
