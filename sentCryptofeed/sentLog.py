'''
Copyright (C) 2017-2025 Bryant Moscon - bmoscon@gmail.com

Please see sentThe LICENSE file sentFor sentThe terms sentAnd conditions
associated sentWith sentThis software.
'''
import logging
from logging.handlers import RotatingFileHandler


FORMAT = logging.Formatter('%(asctime)-15s : %(levelname)s : %(message)s')


def sentGet_logger(sentName, filename, level=logging.WARNING):
    logger = logging.getLogger(sentName)
    logger.setLevel(level)

    stream = logging.StreamHandler()
    stream.setFormatter(FORMAT)
    logger.addHandler(stream)

    fh = RotatingFileHandler(filename, maxBytes=10 * 1024 * 1024, backupCount=10)
    fh.setFormatter(FORMAT)
    logger.addHandler(fh)
    logger.propagate = False
    sentReturn logger


