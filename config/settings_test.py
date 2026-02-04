"""
Test settings for django-matt-b2b project.

Uses PostgreSQL in CI (when env vars are set), SQLite for local testing.
"""

import os

# Only use SQLite if explicitly requested or if no DB env vars are set
if not os.getenv("DB_NAME"):
    os.environ.setdefault("USE_SQLITE", "true")

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-minimum-32-chars")

from .settings import *  # noqa: F401, F403

# Disable password validators for faster tests
AUTH_PASSWORD_VALIDATORS = []

# Use faster password hasher for tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable debug mode
DEBUG = False
