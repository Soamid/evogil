import rx
from rx import Observable, Observer
from rx.subjects import Subject


class ProgressDriverProxy:
    def __init__(self, step_no: int, cost: int):
        self.cost = cost
        self.step_no = step_no


class ProxyAdapter:

    def __init__(self, driver: 'Driver'):
        self.driver = driver

    def receive_proxy(self):
        raise NotImplementedError

    def emit_proxy(self):
        raise NotImplementedError

class ProgressProxyAdapter(ProxyAdapter):

    def __init__(self, driver: 'Driver'):
        super().__init__(driver)

    def emit_proxy(self):
        return ProgressDriverProxy(self.driver.step_no, self.driver.cost)


class StepCountingDriver(type):
    def __init__(cls, name, bases, clsdict):
        step_function = 'step'
        if step_function in clsdict:
            def counting_step(self):
                proxy = clsdict[step_function](self)
                self.step_no += 1
                return proxy

            setattr(cls, step_function, counting_step)


class Driver(object, metaclass=StepCountingDriver):

    def __init__(self, proxy_adapter_factory=ProgressProxyAdapter):
        self.max_budget = None
        self.finished = False
        self.cost = 0
        self.step_no = 0
        self.proxy_adapter = proxy_adapter_factory(self)

    def finalized_population(self):
        raise NotImplementedError

    def step(self) -> ProgressDriverProxy:
        raise NotImplementedError

    def emit_next_proxy(self):
        return self.proxy_adapter.emit_proxy()


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

    def create_job(self, driver: Driver) -> Observable:
        raise NotImplementedError


class BudgetRun(DriverRun):
    def __init__(self, budget: int):
        self.budget = budget

    def create_job(self, driver: Driver) -> Observable:
        return Observable.create(lambda observer: self._start(driver, observer))

    def _start(self, driver: Driver, observer: Observer):
        while driver.cost < self.budget:
            observer.on_next(driver.step())
        observer.on_completed()


class StepsRun(DriverRun):
    def __init__(self, steps: int):
        self.steps = steps

    def create_job(self, driver: Driver):
        return Observable.range(0, self.steps) \
            .map(lambda _: driver.step())


class DriverRx(Driver):
    def steps(self) -> rx.Observable:
        raise NotImplementedError


class DriverRxWrapper(DriverRx):

    def __init__(self, driver: Driver):
        super().__init__()
        self.driver = driver
        self.stream = Subject()

    def step(self):
        proxy = self.driver.step()
        self.stream.on_next(proxy)
        return proxy

    def steps(self) -> rx.Observable:
        return self.stream


class ImgaProxy(ProgressDriverProxy):
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
