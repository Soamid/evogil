class DriverGen:
    def __init__(self):
        pass

    def population_generator(self):
        """ Generator.
        Yiels proxies, allowing them to be modified and to come back (via generator.send())
        to perform migration.

        Each proxy satisfies the following interface:
            proxy.cost
            proxy.finalized_population()
            proxy.get_immigrants()
            proxy.send_emigrants()

        The emigration is actually performed on the driver ONLY IF the proxy with .send_emigrants() called
        is sent back to this generator.

        See: https://gist.github.com/kgadek/e018008be8cfcce313fd
        """
        raise NotImplementedError

    class Proxy:
        def __init__(self, cost):
            self.cost = cost

        def finalized_population(self):
            raise NotImplementedError

        def get_immigrants(self):
            raise NotImplementedError

        def send_emigrants(self, emigrants):
            raise NotImplementedError
