from .base import *
import os

DEBUG = False
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

DATABASES = {
    "default": {
        "ENGINE": "django_prometheus.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "ecommerce"),
        "USER": os.environ.get("DB_USER", "ecommerce"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "ecommerce"),
        "HOST": os.environ.get("DB_HOST", "127.0.0.1"),
        "PORT": os.environ.get("DB_PORT", "5432"),
        "CONN_MAX_AGE": 60,
    }
}

import os
from logging.handlers import RotatingFileHandler

LOG_DIR = "/app/logs"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "core.logger.JSONFormatter",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
        "file_accounts": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_DIR, "accounts.log"),
            "formatter": "json",
            "maxBytes": 10485760,
            "backupCount": 3,
        },
        "file_catalog": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_DIR, "catalog.log"),
            "formatter": "json",
            "maxBytes": 10485760,
            "backupCount": 3,
        },
        "file_cart": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_DIR, "cart.log"),
            "formatter": "json",
            "maxBytes": 10485760,
            "backupCount": 3,
        },
        "file_orders": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_DIR, "orders.log"),
            "formatter": "json",
            "maxBytes": 10485760,
            "backupCount": 3,
        },
        "file_payments": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_DIR, "payments.log"),
            "formatter": "json",
            "maxBytes": 10485760,
            "backupCount": 3,
        },
        "file_core_lock": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_DIR, "core_lock.log"),
            "formatter": "json",
            "maxBytes": 10485760,
            "backupCount": 3,
        },
        "file_aop_metrics": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_DIR, "aop_metrics.log"),
            "formatter": "json",
            "maxBytes": 10485760,
            "backupCount": 3,
        },
        "file_django": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_DIR, "django.log"),
            "formatter": "json",
            "maxBytes": 10485760,
            "backupCount": 3,
        },
        "file_celery": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_DIR, "celery.log"),
            "formatter": "json",
            "maxBytes": 10485760,
            "backupCount": 3,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file_django"],
            "level": "WARNING",
            "propagate": False,
        },
        "celery": {
            "handlers": ["console", "file_celery"],
            "level": "INFO",
            "propagate": False,
        },
        "accounts": {
            "handlers": ["console", "file_accounts"],
            "level": "INFO",
            "propagate": False,
        },
        "catalog": {
            "handlers": ["console", "file_catalog"],
            "level": "INFO",
            "propagate": False,
        },
        "cart": {
            "handlers": ["console", "file_cart"],
            "level": "INFO",
            "propagate": False,
        },
        "orders": {
            "handlers": ["console", "file_orders"],
            "level": "INFO",
            "propagate": False,
        },
        "payments": {
            "handlers": ["console", "file_payments"],
            "level": "INFO",
            "propagate": False,
        },
        "core.lock": {
            "handlers": ["console", "file_core_lock"],
            "level": "INFO",
            "propagate": False,
        },
        "aop.metrics": {
            "handlers": ["console", "file_aop_metrics"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
