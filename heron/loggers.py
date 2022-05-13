import logging
from logging.config import dictConfig

from heron import settings

dictConfig(settings.LOGGING)

IMPORT_LOGGER = logging.getLogger("imports")
EXPORT_EXCEL_LOGGER = logging.getLogger("export_excel")
ERROR_VIEWS_LOGGER = logging.getLogger("error_views")
