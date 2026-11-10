# Architecture

Request flow, app layout and the boundaries a change has to respect. Rules
live in [AGENTS.md](../AGENTS.md); commands in [commands.md](commands.md).

## Runtime

- `manage.py` serves development (`make run`, Django's dev server) and
  management commands.
- `config/asgi.py` is the production entry point; the [Dockerfile](../Dockerfile)
  runs it under granian. `config/wsgi.py` exists for WSGI deployments.
- `config/settings.py` reads the environment through `python-dotenv` (`.env`)
  and holds the `django-matt` configuration (`DJANGO_MATT`, `DJANGO_MATT_JWT`).
  `config/settings_test.py` imports it, forces SQLite unless `DB_NAME` is set,
  and swaps in the fast password hasher.

## Request flow

```
config/urls.py
  /admin/  -> django.contrib.admin
  /api/    -> apps.api.api.urls
                  |
                  v
apps/api.py  DjangoMattAPI instance
  register_auth_routes(api)      apps/users/controllers/routes.py
  register_org_routes(api)       apps/organizations/controllers/routes.py
  health / ready endpoints
                  |
                  v
controllers          async handlers, @jwt_required, Pydantic schemas
                  |
                  v
models               Django ORM (PostgreSQL, SQLite for tests)
```

`apps/api.py` is the only place the `DjangoMattAPI` instance is created. A new
domain gets one `register_<domain>_routes(api)` call there; everything the
domain serves is registered in its own `controllers/routes.py`.

## Layout

|Path|Contents|
| --- | --- |
|`apps/api.py`|API instance, route registration, health and readiness endpoints|
|`apps/core/`|Abstract base models (`BaseModel`, `SoftDeleteModel`), shared management commands (`seed_data`)|
|`apps/users/`|Custom `User` model, auth controller and schemas|
|`apps/organizations/`|`Organization`, `Team`, `Membership`, `Invitation` models, one controller and one schema module per entity, tenant middleware|
|`config/`|Settings, URL configuration, ASGI/WSGI entry points, migration lint config|
|`tests/`|pytest suite and fixtures (see [testing.md](testing.md))|

Each app is a package: `models/`, `schemas/` and `controllers/` hold one module
per entity (`organization.py`, `organization_schema.py`,
`organization_controller.py`) and export through their `__init__.py`.

## Controllers

Controllers subclass `django_matt.core.APIController`, set `tags`, and expose
`@staticmethod` `async` handlers. The handler signature is the contract:

```python
@staticmethod
@jwt_required
async def create_organization(
    request, body: OrganizationCreateSchema
) -> OrganizationSchema:
    ...
```

- The body parameter is the write schema; the return annotation is the
  response model.
- Handlers raise `django_matt` errors (`ValidationAPIError`, auth and
  permission errors) instead of building HTTP responses.
- ORM access is async (`acreate`, `aexists`, `async for`) inside handlers.
- Routes are declared in `controllers/routes.py` as
  `api.post("path", response_model=Schema, tags=["Tag"])(Controller.method)`.
  No business logic in `routes.py`.

## Models

- `apps/core/models.py` provides `UUIDMixin` (UUID primary key),
  `TimestampMixin`, `SoftDeleteMixin`, and the composed `BaseModel` and
  `SoftDeleteModel`. New models inherit one of the composed classes.
- `AUTH_USER_MODEL` is `users.User`.
- Organization-owned models carry an `organization` foreign key; queries in
  controllers filter by it explicitly rather than relying on client input.

## Multi-tenancy

`apps/organizations/middleware.py` provides `TenantContextMiddleware`. It is
not enabled in `MIDDLEWARE` by default. When enabled it resolves the tenant
from `X-Organization-ID`, `X-Organization-Slug`, or the `org_id` query
parameter, checks membership, and attaches `request.tenant`. Controllers that
need tenant scoping read it through `get_current_tenant(request)` /
`require_tenant(request)`.

## Data and migrations

- One migrations package per app, linearized; the policy is in
  [AGENTS.md](../AGENTS.md) and the renumber procedure in
  [.claude/skills/migration-conflict/SKILL.md](../.claude/skills/migration-conflict/SKILL.md).
- `config/migration_lint.py` holds the django-safe-migrations rule exceptions.
- `apps/core/management/commands/seed_data.py` creates sample organizations,
  teams and users for development (`make seed`).
