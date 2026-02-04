"""API configuration and routes."""

from django_matt import MattAPI

from apps.organizations.controllers import register_org_routes
from apps.users.controllers import register_auth_routes

# Create the API instance
api = MattAPI(
    title="Django Matt B2B API",
    version="1.0.0",
    description="A B2B multi-tenant API built with django-matt",
)

# Register routes
register_auth_routes(api)
register_org_routes(api)


# Health check endpoint
@api.get("health", tags=["Health"])
async def health_check(request) -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


# Ready check (with database verification)
@api.get("ready", tags=["Health"])
async def ready_check(request) -> dict:
    """Readiness check with database verification."""
    from django.db import connection

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    return {
        "status": "healthy" if db_status == "healthy" else "unhealthy",
        "database": db_status,
    }
