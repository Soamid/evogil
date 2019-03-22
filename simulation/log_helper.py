import logging
from logging import StreamHandler

LOG_PATH = 'evogil.log'


def init():
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
