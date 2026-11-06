"""Settings for the migration checks (dev dependency group only).

`makemigrations --check --dry-run` and `check_migrations` (django-safe-migrations)
need no database. scripts/db/check_migrations.py and the CI migrations job
select this module; production never imports it.
"""

from .settings import *  # noqa: F401, F403
from .settings import INSTALLED_APPS as _APPS

INSTALLED_APPS = [*_APPS, "django_safe_migrations"]

# The migration checks need no URLs; an empty value skips the URL system check,
# so an API import error never hides a migration problem.
ROOT_URLCONF = ""

# The one place for django-safe-migrations rule exceptions. Inline
# `# safe-migrations: ignore` comments are banned (scripts/db/check_migrations.py).
# Existing findings sit in scripts/baselines/migration-safety.json. Keep a
# rule exception here short, with the reason beside it.
SAFE_MIGRATIONS: dict[str, object] = {
    "DISABLED_RULES": [],
}
