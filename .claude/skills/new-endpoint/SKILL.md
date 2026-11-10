---
name: new-endpoint
description: Add or change an endpoint in the django-matt API - Pydantic schema, controller handler, route registration and pytest coverage. Use when adding a route under /api/ or changing a request/response shape.
---

# Add an endpoint

1. **Schema.** Add the request/response models to
   `apps/<domain>/schemas/<entity>_schema.py` and export them from
   `apps/<domain>/schemas/__init__.py` (`__all__`).
2. **Model** (new persistence only). Add `apps/<domain>/models/<entity>.py`
   inheriting `BaseModel` or `SoftDeleteModel` from `apps/core/models.py`,
   export it from `models/__init__.py`, then run `make migrations` followed by
   `make migrations-check`.
3. **Handler.** Add a `@staticmethod` `async` method to
   `apps/<domain>/controllers/<entity>_controller.py`:
   - `@jwt_required` unless the route is public, plus the role helper from
     `controllers/utils.py` when the route is admin-only.
   - The write schema is a parameter
     (`body: OrganizationCreateSchema`); the return annotation is the response
     schema.
   - Raise `django_matt` errors (`ValidationAPIError`, ...) for expected
     failures; do not build responses.
   - Use the async ORM API (`acreate`, `aexists`, `async for`).
4. **Route.** Register it in `apps/<domain>/controllers/routes.py`:

   ```python
   api.post(
       "organizations",
       response_model=OrganizationSchema,
       tags=["Organizations"],
   )(OrganizationController.create_organization)
   ```

   A new domain needs one `register_<domain>_routes(api)` call in
   `apps/api.py`.
5. **Test.** Add cases to `tests/test_<domain>.py` with the existing fixtures
   (`authenticated_client`, `member_client`, `organization`, ...). Cover the
   success path, the authorization failure, and validation of the body.
6. **Check.** `make lint` and `make test-fast`; `make test` for coverage.

Reference: [docs/architecture.md](../../../docs/architecture.md) and
[docs/code-standards.md](../../../docs/code-standards.md).
