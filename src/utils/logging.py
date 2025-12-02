import logging, sys

def setup_logger():
    fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format=fmt)
    return logging.getLogger("gridbot")
