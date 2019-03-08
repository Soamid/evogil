from logging import StreamHandler
import logging
from logging.handlers import QueueHandler

LOG_PATH = 'evogil.log'

def init_listener():
    root = logging.getLogger()

    # console
    logging.basicConfig(level=logging.DEBUG)
    h = StreamHandler()
    f = logging.Formatter('%(asctime)s%(msecs)d %(process)d %(name)s %(levelname)s %(message)s',
                          datefmt='%Y-%m-%d %H:%M:%S')
    h.setFormatter(f)
    root.addHandler(h)

    # file
    h = logging.FileHandler(LOG_PATH, encoding='utf-8')
    f = logging.Formatter('%(asctime)s%(msecs)d %(process)d %(name)s %(levelname)s %(message)s',
                          datefmt='%Y-%m-%d %H:%M:%S')
    h.setFormatter(f)
    root.addHandler(h)


def listener(queue, configurer):
    configurer()
    while True:
        record = queue.get()
        if record is None:
            break
        logger = logging.getLogger(record.name)
        logger.handle(record)

def init_worker(queue):
    h = QueueHandler(queue)
    root = logging.getLogger()
    root.addHandler(h)
    root.setLevel(logging.DEBUG)
