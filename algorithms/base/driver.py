import threading
import time

import rx
from rx import Observable
from rx import operators as ops
from rx.core.typing import Observer

from algorithms.base.model import (
    ProgressMessageAdapter,
    ProgressMessage,
    TimeProgressMessage,
)


class StepCountingDriver(type):
    def __init__(cls, name, bases, clsdict):
        step_function = "next_step"
        if step_function in clsdict:

            def counting_step(self):
                proxy = clsdict[step_function](self)
                self.step_no += 1
                return proxy

            setattr(cls, step_function, counting_step)


class Driver(object, metaclass=StepCountingDriver):
    def __init__(self, message_adapter_factory=ProgressMessageAdapter):
        self.max_budget = None
        self.finished = False
        self.cost = 0
        self.step_no = 0
        self.message_adapter = message_adapter_factory(self)

    def shutdown(self):
        pass

    def finalized_population(self):
        raise NotImplementedError

    def next_step(self) -> ProgressMessage:
        self.step()
        return self.message_adapter.emit_result()

    def step(self):
        raise NotImplementedError


class ComplexDriver(Driver):
    def __init__(self, driver_message_adapter_factory, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver_message_adapter_factory = driver_message_adapter_factory


class DriverRun:
    def create_job(self, driver: Driver) -> Observable:
        raise NotImplementedError


class BudgetRun(DriverRun):
    def __init__(self, budget: int):
        self.budget = budget

    def create_job(self, driver: Driver) -> Observable:
        return rx.create(lambda observer, scheduler=None: self._start(driver, observer))

    def _start(self, driver: Driver, observer: Observer):
        while driver.cost < self.budget:
            observer.on_next(driver.next_step())
        observer.on_completed()


class StepsRun(DriverRun):
    def __init__(self, steps: int):
        self.steps = steps

    def create_job(self, driver: Driver):
        return rx.range(0, self.steps).pipe(ops.map(lambda _: driver.next_step()))


class TimeRun(DriverRun):
    def __init__(self, step: int, timeout: int):
        self.timeout = timeout
        self.step = step
        self.step_no = 0
        self.time_elapsed = 0

    def create_job(self, driver: Driver) -> Observable:
        return rx.create(lambda observer, scheduler=None: self._start(driver, observer))

    def _start(self, driver: Driver, observer: Observer):
        previous_result = None
        while self.time_elapsed < self.timeout:
            step_start_time = time.time()
            result = driver.next_step()
            self.time_elapsed += time.time() - step_start_time
            time_elapsed_since_last_emission = self.time_elapsed - (self.step * self.step_no)
            if previous_result:
                for _ in range(0, int(time_elapsed_since_last_emission // self.step)):
                    self.step_no += 1
                    emission_time = self.step_no * self.step
                    if emission_time <= self.timeout:
                        observer.on_next(
                            TimeProgressMessage(self.step_no * self.step, previous_result)
                        )
            previous_result = result

        observer.on_completed()


class DriverRx(Driver):
    def steps(self) -> rx.Observable:
        raise NotImplementedError
