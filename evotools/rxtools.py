import multiprocessing
import os
import time
from concurrent.futures import ProcessPoolExecutor
from typing import Callable

import rx
from rx.scheduler import NewThreadScheduler

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


def observable_worker(obs_provider, queue: multiprocessing.Queue):
    obs_provider().subscribe(on_next=queue.put, on_completed=lambda: queue.put("end"))


def worker(fun, queue: multiprocessing.Queue):
    for i in fun():
        print("doing something in " + str(os.getpid()))
        queue.put(i)


def multiprocess_observable(obs_providers, executor: ProcessPoolExecutor = None):
    def workers(observer, scheduler):
        queue = multiprocessing.Queue()

        for obs_provider in obs_providers:
            p = multiprocessing.Process(
                target=observable_worker, args=[obs_provider, queue]
            )
            p.start()

        ended = 0
        while ended < len(obs_providers):
            msg = queue.get()
            if msg == "end":
                ended += 1
            else:
                observer.on_next(msg)

        observer.on_completed()

    return rx.create(workers)


def prime_number(num):
    # If given number is greater than 1
    if num > 1:

        # Iterate from 2 to n / 2
        for i in range(2, num):

            # If num is divisible by any number between
            # 2 and n / 2, it is not prime
            if (num % i) == 0:
                print(num, "is not a prime number")
                return False
        else:
            print(num, "is a prime number")
            return True

    else:
        print(num, "is not a prime number")
        return False


def f1():
    x = 179424691
    return x, prime_number(x), "end"


def f2():
    x = 179424697
    return x, prime_number(x), "end"


def o1():
    return rx.from_iterable([1, 2, 3])


def o2():
    return rx.from_iterable([4, 5, 6])


if __name__ == "__main__":
    t1 = time.time()
    # multiprocess_observable([o1, o2]).subscribe(on_next=print)
    for x in [179424691, 179424697,179424691, 179424697, 179424697, 179424697, 179424691, 179424697, 179424697, 179424697]:
        print(prime_number(x))
    print("execution time: " + str(time.time() - t1))
    exit()
