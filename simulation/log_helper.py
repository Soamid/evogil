import logging
import logging.config
from logging import StreamHandler

LOG_PATH = "evogil.log"


EVOGIL_LOG_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format':  "%(asctime)s%(msecs)d %(process)d %(name)s %(levelname)s %(message)s",
            'datefmt': "%Y-%m-%d %H:%M:%S"
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            # 'stream': 'ext://sys.stdout',  # Default is stderr
        },
        'file': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.FileHandler',
            'filename': LOG_PATH
        }
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': True
        }
    }
}

def init():
    logging.config.dictConfig(EVOGIL_LOG_CONFIG)
    # root = logging.getLogger()
    # # console
    # logging.basicConfig(level=logging.INFO)
    # root.setLevel(logging.INFO)
    # h = StreamHandler()
    # h.setLevel(logging.INFO)
    # f = logging.Formatter(
    #     "%(asctime)s%(msecs)d %(process)d %(name)s %(levelname)s %(message)s",
    #     datefmt="%Y-%m-%d %H:%M:%S",
    # )
    # h.setFormatter(f)
    # root.addHandler(h)
    #
    # # file
    # h = logging.FileHandler(LOG_PATH, encoding="utf-8")
    # h.setLevel(logging.INFO)
    # f = logging.Formatter(
    #     "%(asctime)s%(msecs)d %(process)d %(name)s %(levelname)s %(message)s",
    #     datefmt="%Y-%m-%d %H:%M:%S",
    # )
    # h.setFormatter(f)
    # root.addHandler(h)
