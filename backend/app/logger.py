import logging
logger = logging.getLogger("library_app")
handler = logging.StreamHandler()
fmt = logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s")
handler.setFormatter(fmt)
logger.addHandler(handler)
logger.setLevel(logging.INFO)
