from typing import List


# TYPE DEFINITIONS

Individual = List[float]

Population = List[Individual]

SubPopulation = Population


# UNIVERSAL MESSAGES #


class ProgressMessage:
    def __init__(self, step_no: int, cost: int):
        self.cost = cost
        self.step_no = step_no


class TimeProgressMessage(ProgressMessage):
    def __init__(self, elapsed_time: int, progress: ProgressMessage):
        super().__init__(progress.step_no, progress.cost)
        self.elapsed_time = elapsed_time


class PopulationMessage(ProgressMessage):
    def __init__(self, population: Population, progress: ProgressMessage):
        super().__init__(progress.step_no, progress.cost)
        self.population = population


# UNIVERSAL MESSAGES ADAPTERS #


class MessageAdapter:
    def __init__(self, driver: "Driver"):
        self.driver = driver

    def emit_result(self):
        raise NotImplementedError


class ProgressMessageAdapter(MessageAdapter):
    def __init__(self, driver: "Driver"):
        super().__init__(driver)

    def emit_result(self):
        return ProgressMessage(self.driver.step_no, self.driver.cost)


class PopulationMessageAdapter(ProgressMessageAdapter):
    def emit_result(self) -> PopulationMessage:
        return PopulationMessage(self.get_population(), super().emit_result())

    def get_population(self):
        raise NotImplementedError
