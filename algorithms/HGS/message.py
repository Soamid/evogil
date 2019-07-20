import uuid
from enum import Enum, auto, unique
from typing import Any

from algorithms.base.model import PopulationMessageAdapter


class OperationType(Enum):
    pass


@unique
class HgsOperation(OperationType):
    START = auto()
    NEW_METAEPOCH = auto()
    METAEPOCH_END = auto()
    CHECK_STATUS = auto()
    POPULATION = auto()
    TRIM_NOT_PROGRESSING = auto()
    TRIM_REDUNDANT = auto()


@unique
class NodeOperation(OperationType):
    RESET = auto()
    NEW_RESULT = auto()
    NEW_METAEPOCH = auto()
    METAEPOCH_END = auto()
    CHECK_STATUS = auto()
    CHECK_RIPE = auto()
    POPULATION = auto()
    TRIM_NOT_PROGRESSING = auto()
    TRIM_REDUNDANT = auto()
    KILL = auto()


class Message:
    def __init__(self, operation: OperationType, data: Any = None):
        self.operation = operation
        self.data = data

    def __str__(self):
        return f"<{self.operation} : {self.data}>"


class HgsMessage(Message):
    def __init__(self, operation: HgsOperation, data: Any = None):
        super().__init__(operation, data)


class NodeMessage(Message):
    def __init__(self, operation: NodeOperation, id: uuid, data: Any = None):
        super().__init__(operation, data)
        self.id = id


class HGSMessageAdapter(PopulationMessageAdapter):
    def nominate_delegates(self):
        raise NotImplementedError


class DefaultHGSMessageAdapter(HGSMessageAdapter):
    def get_population(self):
        return [x.v for x in self.driver.individuals]

    def nominate_delegates(self):
        return [x.v for x in self.driver.front[1]]
