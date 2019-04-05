import logging


class Topology:
    def create(self, size):
        """ :return: Return created topology as adjacency list """
        raise NotImplementedError

    @staticmethod
    def print(t):
        logger = logging.getLogger(__name__)
        for i in range(len(t)):
            logger.debug(str(i) + " : " + str(t[i]))


class TorusTopology(Topology):
    def __init__(self, width):
        self.width = width

    def create(self, size):
        t = []

        N = self.width * int(size / self.width)

        for i in range(N):
            row = int(i / self.width)
            neighbors = []
            neighbors.append((i - 1) % self.width + row * self.width)
            neighbors.append((i + 1) % self.width + row * self.width)
            neighbors.append((i - self.width) % N)
            neighbors.append((i + self.width) % N)

            t.append(neighbors)

        if N < size:
            last_width = size - N

            for i in range(N, size):

                row = int(i / self.width)

                neighbors = set()

                if len(t) > self.width:
                    last = i - self.width
                    last_neighbors = t[last]

                    first = i % self.width
                    first_neighbors = t[first]

                    last_neighbors.remove(first)
                    last_neighbors.append(i)

                    first_neighbors.remove(last)
                    first_neighbors.append(i)

                    neighbors.add(first)
                    neighbors.add(last)

                neighbors.add((i - N - 1) % last_width + row * self.width)
                neighbors.add((i - N + 1) % last_width + row * self.width)

                t.append(neighbors)

            if last_width == 1:
                t[N].remove(N)

        return [set(neighbors) for neighbors in t]
