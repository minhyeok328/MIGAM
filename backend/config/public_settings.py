"""Visitor API only. Collection runs in a separate process with writable settings."""

import os
from django.core.exceptions import ImproperlyConfigured
from .settings import *  # noqa: F403

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if len(SECRET_KEY) < 32:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY must be configured")

ALLOWED_HOSTS = ["migam-home-preview.vercel.app"]
for name in ("VERCEL_URL", "VERCEL_PROJECT_PRODUCTION_URL"):
    host = os.environ.get(name, "")
    if host and "/" not in host and host.endswith(".vercel.app"):
        ALLOWED_HOSTS.append(host)

ROOT_URLCONF = "backend.config.public_urls"
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = 31536000
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "no-referrer"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
DATA_UPLOAD_MAX_MEMORY_SIZE = 64 * 1024
DATABASES["default"]["OPTIONS"] = {"uri": True}  # noqa: F405
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {"discard": {"class": "logging.NullHandler"}},
    "root": {"handlers": ["discard"], "level": "CRITICAL"},
}
