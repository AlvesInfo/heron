"""Module pour logger
Commentaire:
created at: 2022-07-12
created by: Paulo ALVES
modified at: 2022-07-12
modified by: Paulo ALVES
"""
import logging
from logging.config import dictConfig
from heron.settings import LOGGING

dictConfig(LOGGING)

LOGGER_PRODUCTION = logging.getLogger("production")
