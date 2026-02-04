"""
Test settings for django-matt-b2b project.

Uses SQLite for testing to avoid requiring PostgreSQL.
"""

import os

# Force SQLite before importing base settings
os.environ["USE_SQLITE"] = "true"
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest")

from .settings import *  # noqa: F401, F403

# Override database to ensure SQLite is used
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test_db.sqlite3",  # noqa: F405
    }
}

# Disable password validators for faster tests
AUTH_PASSWORD_VALIDATORS = []

# Use faster password hasher for tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable debug mode
DEBUG = False
