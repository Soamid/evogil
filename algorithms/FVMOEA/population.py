from typing import List, Set, Tuple

Vector = Tuple[float]


class Individual(object):
    def __init__(self, vector: Vector):
        self.vector = vector
        self.objectives = []  # type: Vector

    def __hash__(self):
        return hash(self.vector)

    def __eq__(self, other):
        if isinstance(other, Individual):
            return self.vector == other.vector
        else:
            return False

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return str(self.vector)


Population = Set[Individual]
Dimensions = List[List[int]]
Objectives = List[Vector]
