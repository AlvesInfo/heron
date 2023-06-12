import logging
from logging.config import dictConfig

from heron import settings

dictConfig(settings.LOGGING)

LOGGER_IMPORT = logging.getLogger("imports")
LOGGER_EXPORT_EXCEL = logging.getLogger("export_excel")
LOGGER_VIEWS = logging.getLogger("error_views")
LOGGER_DJANGO = logging.getLogger("django")
LOGGER_PRODUCTION = logging.getLogger("production")
LOGGER_CONNEXION = logging.getLogger("connexion")
LOGGER_TIMER_HERON = logging.getLogger("timer_heron")
LOGGER_EDI = logging.getLogger("edi")
LOGGER_LOADER = logging.getLogger("loader")
LOGGER_VALIDATION = logging.getLogger("validation")
LOGGER_POSTGRES_SAVE = logging.getLogger("postgres_save")
LOGGER_INVOICES = logging.getLogger("invoices_flux")
LOGGER_EMAIL = logging.getLogger("send_email")
