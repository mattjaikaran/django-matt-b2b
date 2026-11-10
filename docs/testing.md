# Testing

The suite is pytest with pytest-django, pytest-asyncio and pytest-xdist. It
exercises the API through `django_matt.testing.APITestClient`; there is no
browser or frontend layer, so an API test through that client is the
end-to-end test for this repo.

## Configuration

- `DJANGO_SETTINGS_MODULE=config.settings_test` (set in
  `[tool.pytest.ini_options]`).
- `config/settings_test.py` falls back to SQLite when `DB_NAME` is unset,
  disables password validators and uses `MD5PasswordHasher`.
- `asyncio_mode = "auto"`, function-scoped event loop.
- Test files are discovered in `tests/` as `test_*.py`.
- CI (`.github/workflows/ci.yml`) runs the suite against PostgreSQL 16 with
  `uv run pytest -v --cov=apps --cov-report=xml`.

## Layout and fixtures

`tests/conftest.py` builds the fixture graph:

|Fixture|Provides|
| --- | --- |
|`user`, `user2`|Plain users|
|`admin_user`, `member_user`|Organization admin and non-owner member|
|`organization`, `team`|An organization owned by `user`, and a team in it|
|`api_client`|Unauthenticated `APITestClient`|
|`authenticated_client`, `authenticated_client2`, `member_client`|Clients with `force_authenticate` already applied|

Tests live in `tests/test_<domain>.py` (`test_auth.py`,
`test_organizations.py`). Add new cases there and reuse the fixtures instead of
creating users inline.

## Commands

```bash
make test-fast                          # uv run pytest -v
make test                               # with coverage, HTML report in htmlcov/
uv run pytest tests/test_auth.py        # one module
uv run pytest -k login                  # by name
uv run pytest -n auto                   # parallel, via pytest-xdist
```

`make test-watch` runs `pytest-watch`, which is not in the `dev` dependency
group; use `uv run pytest -f` (pytest-xdist loop-on-fail) instead.

`make test` prints a term-missing coverage report; `apps` is the source, with
migrations and tests omitted.

## Policy

The testing rules are in [AGENTS.md](../AGENTS.md#testing); this page covers
the mechanics.
