from enum import Enum, auto, unique
from typing import Any

from algorithms.base.model import PopulationMessageAdapter


@unique
class HgsOperation(Enum):
    START = auto()
    NEW_METAEPOCH = auto()
    METAEPOCH_END = auto()
    CHECK_ALL_ALIVE = auto()
    POPULATION = auto()

@unique
class NodeOperation(Enum):
    RESET = auto()
    NEW_RESULT = auto()
    NEW_METAEPOCH = auto()
    METAEPOCH_END = auto()
    CHECK_ALIVE = auto()
    CHECK_RIPE = auto()
    POPULATION = auto()


class HgsMessage:
    def __init__(self, operation: HgsOperation, data: Any = None):
        self.operation = operation
        self.data = data

    def __str__(self):
        return f"<{self.operation} : {self.data}>"


class NodeMessage:
    def __init__(self, operation: NodeOperation, data: Any = None):
        self.operation = operation
        self.data = data

    def __str__(self):
        return f"<{self.operation} : {self.data}>"


class HGSMessageAdapter(PopulationMessageAdapter):
    def nominate_delegates(self):
        raise NotImplementedError


class DefaultHGSMessageAdapter(HGSMessageAdapter):
    def get_population(self):
        return [x.v for x in self.driver.individuals]

    def nominate_delegates(self):
        return [x.v for x in self.driver.front[1]]
