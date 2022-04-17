from pathlib import Path
import logging
from logging.config import dictConfig

logs_dir = Path("/var/log/heron")

if logs_dir.is_dir():
    VAR_LOG_DIR = Path("/var/log/heron").resolve()
    Path.mkdir(VAR_LOG_DIR, exist_ok=True)

else:
    VAR_LOG_DIR = Path("./log").resolve()
    Path.mkdir(VAR_LOG_DIR, exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": (
                "[data_flux] : "
                "[%(asctime)s] %(levelname)s : %(message)s : "
                "%(filename)s : "
                "%(funcName)s : "
                "[ligne : %(lineno)s] : "
                "%(process)d : "
                "%(thread)d"
            ),
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        # Send in console
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        # Send in loader data_flux
        "loader_logfile": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": f"{VAR_LOG_DIR}/loaders_flux.log",
            "formatter": "verbose",
        },
        # Send in validation data_flux
        "validation_logfile": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": f"{VAR_LOG_DIR}/validation_flux.log",
            "formatter": "verbose",
        },
        # Send in postgres_save data_flux
        "postgres_save_logfile": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": f"{VAR_LOG_DIR}/postgres_save_flux.log",
            "formatter": "verbose",
        },
    },
    "loggers": {
        # all messages
        "": {"handlers": ["console"], "propagate": True},
        "loader": {"handlers": ["loader_logfile"], "propagate": True},
        "validation": {"handlers": ["validation_logfile"], "propagate": True},
        "postgres_save": {"handlers": ["postgres_save_logfile"], "propagate": True},
    },
}

dictConfig(LOGGING)

LOADER_LOGGER = logging.getLogger("loader")
VALIDATION_LOGGER = logging.getLogger("validation")
POSTGRES_SAVE_LOGGER = logging.getLogger("postgres_save")
