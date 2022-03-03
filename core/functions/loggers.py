import logging
from logging.config import dictConfig
from pathlib import Path

from core.functions.functions_setups import settings

excel_log_file = Path(settings.LOG_DIR) / "excel_log.log"
excel_log_file.open("a").close()

xml_log_file = Path(settings.LOG_DIR) / "xml_log.log"
xml_log_file.open("a").close()

import_log_file = Path(settings.LOG_DIR) / "import_log.log"
import_log_file.open("a").close()

postgres_log_file = Path(settings.LOG_DIR) / "postgres_log.log"
postgres_log_file.open("a").close()

dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "verbose": {
                "format": (
                    "[HERON] : "
                    "[%(asctime)s] %(levelname)s : %(message)s : "
                    "%(filename)s : "
                    "%(funcName)s : "
                    "[ligne : %(lineno)s] : "
                    "%(process)d : "
                    "%(thread)d"
                ),
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "simple": {
                "format": "[%(asctime)s] %(levelname)s : %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            # Send in console
            "console": {"level": "INFO", "class": "logging.StreamHandler", "formatter": "simple"},
            # Send in development_logfile
            "excel_handler": {
                "level": "INFO",
                "class": "logging.FileHandler",
                "filename": excel_log_file.resolve(),
                "formatter": "verbose",
            },
            "xml_handler": {
                "level": "INFO",
                "class": "logging.FileHandler",
                "filename": excel_log_file.resolve(),
                "formatter": "verbose",
            },
            "import_handler": {
                "level": "INFO",
                "class": "logging.FileHandler",
                "filename": excel_log_file.resolve(),
                "formatter": "verbose",
            },
            "postgres_handler": {
                "level": "INFO",
                "class": "logging.FileHandler",
                "filename": excel_log_file.resolve(),
                "formatter": "verbose",
            },
        },
        "loggers": {
            # all messages
            # 5xx ERRROR and 4xx WARNING
            "": {"handlers": ["console"], "propagate": True},
            "excel_log": {"handlers": ["excel_handler"], "level": "INFO", "propagate": False},
            "xml_log": {"handlers": ["xml_handler"], "level": "INFO", "propagate": False},
            "import_log": {"handlers": ["import_handler"], "level": "INFO", "propagate": False},
            "postgres_log": {"handlers": ["postgres_handler"], "level": "INFO", "propagate": False},
        },
    }
)

EXCEL_LOGGER = logging.getLogger("excel_log")
XML_LOGGER = logging.getLogger("xml_log")
IMPORT_LOGGER = logging.getLogger("import_file")
POSTGRES_LOGGER = logging.getLogger("import_file")
