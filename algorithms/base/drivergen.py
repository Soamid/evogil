import rx
from rx.subjects import Subject


class DriverProxy:
    def __init__(self, driver: 'Driver', cost: int):
        self.cost = cost
        self.driver = driver

    def finalized_population(self):
        """
        :return: Returns finalized population
        """
        raise NotImplementedError


class Driver:
    max_budget = None

    def __init__(self):
        self.finished = False
        self.cost = 0
        self.step_no = 0

    def next_generation(self, f):
        def wrapper(self):
            f()
            self.step_no += 1

        return wrapper

    @next_generation
    def step(self) -> DriverProxy:
        raise NotImplementedError


class DriverGen(Driver):
    max_budget = None

    def __init__(self):
        super().__init__()
        self.finished = False

    def population_generator(self):
        """ Generator.
        Yiels proxies, allowing them to be modified and to come back (via generator.send())
        to perform migration.

        Each proxy satisfies the following interface:
            proxy.cost
            proxy.finalized_population()
            proxy.current_population()
            proxy.deport_emigrants(immigrants)
            proxy.assimilate_immigrants(emigrants)
            proxy.nominate_delegates(delegates_no)
        """
        raise NotImplementedError


class DriverRun:

    def start(self, driver: Driver):
        raise NotImplementedError


class BudgetRun(DriverRun):
    def __init__(self, budget: int):
        self.budget = budget

    def start(self, driver: Driver):
        while driver.cost < self.budget:
            driver.step()


class StepsRun(DriverRun):
    def __init__(self, steps: int):
        self.steps = steps

    def start(self, driver: Driver):
        for i in range(self.steps):
            driver.step()


class DriverRx(Driver):

    def __init__(self, driver: Driver):
        super().__init__()
        self.driver = driver
        self.stream = Subject()

    def step(self):
        proxy = self.driver.step()
        self.stream.on_next(proxy)

    def steps(self) -> rx.Observable:
        return self.stream


class ImgaProxy(DriverProxy):
    def __init__(self, driver: Driver, cost: int):
        super().__init__(driver, cost)

    def current_population(self):
        """
        :return: Returns individuals selected from the current population.
        """
        raise NotImplementedError

    def deport_emigrants(self, immigrants):
        """
        :param immigrants: Individuals that shall be removed from the population.
        :return: Immigrants objects removed from the population. Objects should be equal to immigrants,
        but they may be expressed in driver-specific model form.
        """
        raise NotImplementedError

    def assimilate_immigrants(self, emigrants):
        """
        :param emigrants: Individuals that shall be assimilated into the population, expressed in driver-specific model form.
        :return: Does not return. This Proxy object shall be passed back to the generator.
        """
        raise NotImplementedError

    def nominate_delegates(self):
        """
        :return: returns a reasonable number of delegates - best individuals that the population is able to provide.
        """
        raise NotImplementedError
