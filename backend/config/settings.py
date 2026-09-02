import os
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "migam-local-development-only")
DEBUG = False
USE_TZ = True
TIME_ZONE = "Asia/Seoul"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

INSTALLED_APPS = [
    "rest_framework",
    "backend.apps.sources",
    "backend.apps.data_quality",
    "backend.apps.catalog",
    "backend.apps.discovery",
]

ROOT_URLCONF = "backend.config.urls"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "UNAUTHENTICATED_USER": None,
}

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.environ.get(
            "MIGAM_DB_PATH",
            str(REPOSITORY_ROOT / "backend" / "db.sqlite3"),
        ),
    }
}
