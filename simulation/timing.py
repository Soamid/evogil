import contextlib
from logging import DEBUG
import time


@contextlib.contextmanager
def process_time(lst):
    start = time.process_time()
    yield
    end = time.process_time()
    lst.append(end - start)


@contextlib.contextmanager
def system_time(lst):
    start = time.perf_counter()
    yield
    end = time.perf_counter()
    lst.append(end - start)


@contextlib.contextmanager
def log_time(ctx, log, msg, out=None, loglvl=None):
    if not loglvl:
        loglvl = DEBUG
    if out is None:
        out = []
    with ctx(out):
        yield
    log.log(loglvl, msg.format(time_res=out[-1]))
