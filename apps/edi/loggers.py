import logging
from logging.config import dictConfig

from apps.core.functions.functions_setups import settings

dictConfig(settings.LOGGING)

EDI_LOGGER = logging.getLogger("edi")
