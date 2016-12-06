#!/usr/bin/python
import logging

LOGGING_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(format=LOGGING_FORMAT, level=logging.CRITICAL)
top_logger = logging.getLogger(__name__)


def configure_logging(verbose=False, filename=False):
    if verbose:
        top_logger.setLevel(logging.DEBUG)

    if filename:
        fh = logging.FileHandler(filename)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter(LOGGING_FORMAT))
        top_logger.addHandler(fh)

