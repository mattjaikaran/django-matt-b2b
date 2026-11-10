# Code standards

`pyproject.toml` is the source of truth for tool configuration; this page
explains the conventions the code follows. Policy lives in
[AGENTS.md](../AGENTS.md).

## Formatting and linting

- ruff, configured in `[tool.ruff]`: Python 3.12 target, line length 100,
  double quotes, formatted with `ruff format`. The repo does not keep a
  separate style guide; ruff decides.
- Enabled rule sets: `E`, `W`, `F`, `I`, `N`, `UP`, `B`, `C4`, `SIM`, `ASYNC`.
  Ignored: `E501` (the formatter owns wrapping), `B008` (`Depends()` defaults),
  `B904` (clean API errors), `SIM102`. Tests may use bare `assert`.
- Import order is enforced with a dedicated `django` section between the
  standard library and third-party packages; `apps` and `config` are first
  party.
- `make lint` runs `uv run ruff check .` and
  `uv run mypy apps/ --ignore-missing-imports`. mypy is non-strict, with
  `warn_return_any`; `migrations/` and `tests/` are excluded.
- `make format` runs `ruff format .` then `ruff check --fix .`.

## Python conventions

- `from __future__ import annotations` at the top of controllers, schemas and
  anything else with modern annotations.
- Type hints on public functions and handlers; return annotations double as
  the API response model.
- Absolute imports (`from apps.users.models import User`) across apps;
  relative imports inside an app package (`from ..models import Team`,
  `from .utils import require_admin`).
- Docstrings on modules, classes and handlers; one line is enough.
- Handlers are `async def`; keep blocking calls out of them. Use the async
  ORM API (`acreate`, `aexists`, `aget`, `async for`).
- Raise `django_matt` API errors for expected failures; do not return error
  payloads by hand and do not log tokens.

## Layering

|Layer|Responsibility|
| --- | --- |
|`controllers/routes.py`|Path, response model and tags only|
|`controllers/<entity>_controller.py`|Validation, authorization, transaction, ORM access|
|`schemas/<entity>_schema.py`|Pydantic request/response models, exported from `schemas/__init__.py`|
|`models/<entity>.py`|Fields, relations, small properties; exported from `models/__init__.py`|

- A controller method is the unit of authorization (`@jwt_required`, role
  checks through `controllers/utils.py`), not the route.
- A schema never imports a controller; a model never imports a schema.
- Cross-entity work stays in the controller for the entity that owns the
  request path.

## Naming

- `OrganizationController`, `OrganizationSchema`, `OrganizationCreateSchema`.
- Modules: `<entity>.py`, `<entity>_schema.py`, `<entity>_controller.py`.
- Route groups: `register_<domain>_routes(api)`, called once from
  `apps/api.py`.
- Tests: `tests/test_<domain>.py`, test functions named for the behavior.

## Size

`scripts/check_file_length.py` runs in pre-commit and prints the offending
file and its line count when it fails. When a module gets close, split it by
entity the way `apps/organizations/` splits models and controllers, rather
than adding a section to an existing file.
