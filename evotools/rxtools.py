from concurrent.futures import ProcessPoolExecutor
from typing import Callable

import rx
from rx.concurrency import NewThreadScheduler

default_process_executor = ProcessPoolExecutor()


def configure_default_executor(number_of_processes: int):
    global default_process_executor
    default_process_executor = ProcessPoolExecutor(number_of_processes)


def shutdown_default_executor():
    default_process_executor.shutdown()


def from_process(
    worker: Callable, *args, executor: ProcessPoolExecutor = None, **kwargs
):
    executor = executor if executor else default_process_executor

    def run_as_process():
        future = executor.submit(worker, *args, **kwargs)
        return future.result()

    return rx.from_callable(run_as_process, NewThreadScheduler())
