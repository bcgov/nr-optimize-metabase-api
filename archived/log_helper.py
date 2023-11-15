import logging

LOGGER = logging.getLogger("DEBUG")
LOGGER = logging.getLogger("WARNING")
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)
hndlr = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(lineno)d - %(message)s')
hndlr.setFormatter(formatter)
LOGGER.addHandler(hndlr)
