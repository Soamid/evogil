import logging
from pathlib import Path


def init_loggers():
    logger_console_output = logging.StreamHandler()
    logger_console_output.setLevel(logging.INFO)
    logger_console_output.setFormatter(
        logging.Formatter(
            '%(asctime)s %(name)s %(levelname)s: %(message)s',
            datefmt='%H:%M:%S'))

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(logger_console_output)


def get_logger(name):
    logger_file_output = logging.FileHandler(str(Path('logs', name + '.log')), encoding='utf-8')
    logger_file_output.setLevel(logging.DEBUG)
    logger_file_output.setFormatter(
        logging.Formatter(
            '%(asctime)s%(msecs)d pr:%(process)d %(name)s %(levelname)s msg:%(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'))

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logger_file_output)

    return logger
