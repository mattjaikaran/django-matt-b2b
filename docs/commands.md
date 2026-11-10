# Commands

`make help` lists every target; this page adds the prerequisites and the
commands behind the targets used day to day. Run everything from the repo
root.

## Prerequisites

- Python 3.12+ (CI uses 3.13) and [uv](https://docs.astral.sh/uv/).
- A GitHub SSH key. `pyproject.toml` pins `django-matt` to
  `git+ssh://git@github.com/mattjaikaran/django-matt`, so `uv sync` installs
  that dependency over SSH; CI supplies the key through
  `secrets.SSH_PRIVATE_KEY`.
- The interpreter must have a `psycopg-binary` wheel (cp312-cp314). If uv picks
  a newer Python (3.15 has no wheels yet), pin it:
  `uv sync --dev --python 3.12` or `UV_PYTHON=3.12 make dev`.
- PostgreSQL 16 for `make migrate`, `make run` and `make test` against a real
  database: `make docker-up` starts Postgres and Redis, or set `DB_NAME`,
  `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`. `USE_SQLITE=true` switches
  the settings to SQLite; the test settings fall back to SQLite on their own.

## Setup and run

|Target|Runs|Notes|
| --- | --- | --- |
|`make install`|`uv sync`|Production dependencies|
|`make dev`|`uv sync --dev`|Adds ruff, mypy, pytest and pre-commit|
|`make setup`|`install` + `migrate`|Then `make superuser` and `make run`|
|`make run`|`uv run python manage.py runserver`|Development server on :8000; docs at `/api/docs`|
|`make migrate`|`uv run python manage.py migrate`|Needs the database|
|`make migrations`|`uv run python manage.py makemigrations`|Then `make migrations-check`|
|`make superuser`|`createsuperuser`|Interactive|
|`make seed`|`manage.py seed_data`|Sample orgs, teams and users|
|`make shell` / `make dbshell`|`manage.py shell` / `dbshell`|Interactive|

## Quality

|Target|Runs|
| --- | --- |
|`make lint`|`uv run ruff check .` and `uv run mypy apps/ --ignore-missing-imports`|
|`make format`|`uv run ruff format .` and `uv run ruff check --fix .`|
|`make test-fast`|`uv run pytest -v`|
|`make test`|`uv run pytest -v --cov=apps --cov-report=term-missing --cov-report=html`|
|`make pre-commit`|`uv run pre-commit run --all-files`|
|`make docs-check`|`python3 scripts/check_agent_docs.py`|
|`make migrations-check`|`python3 scripts/db/check_migrations.py` (no-merge, leaf, safe-migrations)|
|`make migrations-renumber`|`python3 scripts/db/renumber_migrations.py` (dry run; `ARGS=--apply` writes)|

`make lint` runs both tools, and both pass on `apps/`; the type-check CI job
is blocking.

## Build

- `uv build` builds the wheel and sdist into `dist/` (hatchling, packages
  `apps` and `config`).
- `make docker-build` builds the API image; `make docker-all` runs the full
  compose stack and `make docker-dev` the `dev` profile. These need a Docker
  daemon.

## Other targets

`make docker-down`, `docker-logs`, `docker-clean` manage the compose stack.
`make sync-types` exports TypeScript types from the API and `make requirements`
compiles requirements files; both are template utilities that CI does not use.
`make clean` removes caches and build output.

## Behind the targets

The wrappers stay thin so the underlying commands work directly:

```bash
uv run python manage.py <command>
uv run pytest
uv run ruff check . && uv run ruff format --check .
uv run mypy apps/ --ignore-missing-imports
python3 scripts/check_agent_docs.py
python3 scripts/db/check_migrations.py --base origin/main
```
