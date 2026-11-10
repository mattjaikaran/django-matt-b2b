# Agent instructions

`AGENTS.md` is the single source of agent instructions for this repo. `CLAUDE.md`
only imports it, long reference material lives in `docs/`, and step-by-step
procedures live in `.claude/skills/`. A nested `AGENTS.md` would win for its
directory; there is none today.

## Project

A B2B multi-tenant Django API template built on
[django-matt](https://github.com/mattjaikaran/django-matt). Django 6, Python
3.12+, PostgreSQL (SQLite for tests or `USE_SQLITE=true`), uv, granian,
Pydantic schemas, JWT auth, OpenAPI at `/api/docs`. Layout and request flow:
[docs/architecture.md](docs/architecture.md).

## Commands

Run from the repo root. `make help` lists every target; the prerequisites and
the commands behind each target are in [docs/commands.md](docs/commands.md).

| Task | Command |
| --- | --- |
| Install prod / dev dependencies | `make install` / `make dev` |
| Build | `uv build` |
| Run the API on :8000 | `make run` |
| Apply migrations | `make migrate` |
| Create a migration | `make migrations` |
| Check migrations | `make migrations-check` |
| Test (fast / with coverage) | `make test-fast` / `make test` |
| Lint (ruff + mypy) | `make lint` |
| Format | `make format` |
| Check this file and its links | `make docs-check` |
| Pre-commit hooks | `make pre-commit` |

`pyproject.toml` pins `django-matt` to
`git+ssh://git@github.com/mattjaikaran/django-matt`, so install, lint and test
need a GitHub SSH key (CI passes `secrets.SSH_PRIVATE_KEY`). Postgres for
`make migrate` and `make test` comes from `make docker-up` or the `DB_*`
environment variables; `config/settings_test.py` falls back to SQLite when
`DB_NAME` is unset.

## Architecture and code standards

Read [docs/architecture.md](docs/architecture.md) and
[docs/code-standards.md](docs/code-standards.md) before a non-trivial change.

- One app per domain: `apps/<domain>/` with `models/`, `schemas/` and
  `controllers/` packages, one module per entity, and a `controllers/routes.py`
  that registers the group in `apps/api.py`.
- Controllers are async and decorated (`@jwt_required`); request bodies and
  responses are Pydantic schemas from the same app; persistence goes through
  the Django ORM.
- Files stay under 400 lines (`scripts/check_file_length.py`); split by entity
  instead of growing a module.

## Testing

A behavior change ships with a test that exercises it; a bug fix includes the
regression test; never weaken, skip or delete an existing test to make the
suite pass. Use `make test-fast` in the loop and `make test` for coverage.
Suite layout, fixtures and settings: [docs/testing.md](docs/testing.md).

## Migrations

- Migrations are linearized, never merged: never run `makemigrations --merge`
  and never add a merge migration.
- Never edit a migration that is already on `origin/main`; add a new one.
- After changing a model or a migration, run `make migrations-check` before
  you push.
- A conflict (two leaves, or a number that clashes with `origin/main`) is
  fixed by renumbering: follow
  [.claude/skills/migration-conflict/SKILL.md](.claude/skills/migration-conflict/SKILL.md).
- django-safe-migrations exceptions live in `config/migration_lint.py`;
  existing findings sit in `scripts/baselines/migration-safety.json`. An inline
  `# safe-migrations: ignore` comment fails `make migrations-check`.

## Git and commits

- Conventional Commits: `type(scope): Imperative summary`. Subject at most 50
  characters (`git log -1 --format=%s | awk '{print length}'`), body wrapped
  at 72, one logical change per commit.
- Never commit local or generated artifacts: `.env`, `/types/`, caches,
  `db.sqlite3`, `dist/`.
- Never bypass checks with `--no-verify`, and never edit a check to fit a
  change; fix the change.

## Specs (agent-run)

Unattended work starts from a spec in `tasks/specs/`. A spec names exact paths
in `Files owned`; the agent-run gate fails on any changed file outside that
list and on any migration the spec did not list. When the work needs a path or
a design decision the spec does not grant, stop and report the gap instead of
widening scope. Format and lifecycle: [tasks/specs/README.md](tasks/specs/README.md).

## Security

- Secrets never enter the repo: copy `.env.example` to `.env` (gitignored).
  The `SECRET_KEY` fallback in `config/settings.py` is development-only.
- Never log access or refresh tokens; JWT lifetimes live in `DJANGO_MATT_JWT`
  in `config/settings.py`.
- Scope every organization query to the organization on the request, never to
  a client-supplied id.
- `detect-private-key` runs in pre-commit. A leaked credential is rotated, not
  just deleted from one commit.

## Agent docs maintenance

- Edit `AGENTS.md`, not `CLAUDE.md`; Claude Code reads `AGENTS.md` through
  `CLAUDE.md`'s `@AGENTS.md` import. No rule is copied into a second file.
- Procedures go in `.claude/skills/<name>/SKILL.md` with `name` and
  `description` frontmatter; facts and rules stay here.
- Run `make docs-check` after editing agent docs: it fails when `AGENTS.md` is
  missing, when `CLAUDE.md` does not import it, or when a relative link does
  not resolve.
