"""Loopback-only local API settings; never use for a public deployment."""

import os

from .settings import *  # noqa: F403


ALLOWED_HOSTS = ["127.0.0.1", "localhost", "[::1]"]
MIGAM_DEMO_MODE = os.environ.get("MIGAM_DEMO_MODE") == "1"
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"discard": {"class": "logging.NullHandler"}},
    "loggers": {
        "django.server": {"handlers": ["discard"], "propagate": False},
        "django.request": {"handlers": ["discard"], "propagate": False},
    },
}
