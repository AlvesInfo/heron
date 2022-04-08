import logging
from logging.config import dictConfig

from apps.core.functions.functions_setups import settings

dictConfig(settings.LOGGING)

IMPORT_LOGGER = logging.getLogger("imports")
