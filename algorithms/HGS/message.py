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
    TRIM_NOT_PROGRESSING_END = auto()
    TRIM_REDUNDANT = auto()
    TRIM_REDUNDANT_END = auto()
    HELLO = auto()
    REGISTER_NODE = auto()
    REGISTER_NODE_END = auto()
    RELEASE_SPROUTS = auto()
    RELEASE_SPROUTS_END = auto()


@unique
class NodeOperation(OperationType):
    RESET = auto()
    KILL = auto()
    NEW_RESULT = auto()
    NEW_METAEPOCH = auto()
    METAEPOCH_END = auto()
    CHECK_STATUS = auto()
    CHECK_RIPE = auto()
    POPULATION = auto()
    TRIM_NOT_PROGRESSING = auto()
    TRIM_NOT_PROGRESSING_END = auto()
    RELEASE_SPROUTS = auto()
    RELEASE_SPROUTS_END = auto()


class Message:
    def __init__(self, operation: OperationType, id: uuid, data: Any = None):
        self.operation = operation
        self.id = id if id else uuid.uuid4()
        self.data = data

    def __str__(self):
        return f"<{self.operation} : {self.data}>"


class HgsMessage(Message):
    def __init__(self, operation: HgsOperation, id: uuid=None, data: Any = None):
        super().__init__(operation, id, data)


class NodeMessage(Message):
    def __init__(self, operation: NodeOperation, id: uuid=None, data: Any = None):
        super().__init__(operation, id, data)


class HGSMessageAdapter(PopulationMessageAdapter):
    def nominate_delegates(self):
        raise NotImplementedError


class DefaultHGSMessageAdapter(HGSMessageAdapter):
    def get_population(self):
        return [x.v for x in self.driver.individuals]

    def nominate_delegates(self):
        return [x.v for x in self.driver.front[1]]
