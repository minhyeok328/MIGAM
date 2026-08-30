import os
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "migam-local-development-only")
DEBUG = False
USE_TZ = True
TIME_ZONE = "Asia/Seoul"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

INSTALLED_APPS = [
    "backend.apps.sources",
    "backend.apps.data_quality",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.environ.get(
            "MIGAM_DB_PATH",
            str(REPOSITORY_ROOT / "backend" / "db.sqlite3"),
        ),
    }
}
