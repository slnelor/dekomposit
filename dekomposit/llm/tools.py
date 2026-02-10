import logging

from dekomposit.llm.base_client import Client
from dekomposit.llm.types import Translation


logging.basicConfig(
    datefmt="%d/%m/%Y %H:%M",
    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
