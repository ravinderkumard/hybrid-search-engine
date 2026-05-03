import logging
from pythonjsonlogger import jsonlogger

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("hybrid_search")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()

handler.setFormatter(formatter)
logger.addHandler(handler)