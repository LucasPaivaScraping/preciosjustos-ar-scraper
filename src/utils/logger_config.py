# logger_config.py

import logging


def get_logger(name):
    logger = logging.getLogger(name)
    logger.propagate = False

    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(levelname)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
