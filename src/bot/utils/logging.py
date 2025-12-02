import logging, sys

def setup_logger(name: str = "fgrid"):
    fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format=fmt)
    return logging.getLogger(name)
