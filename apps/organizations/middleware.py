"""Tenant context middleware for multi-tenancy."""

from uuid import UUID

from django.http import HttpRequest
from django.utils.deprecation import MiddlewareMixin

from .models import Membership, Organization


class TenantContext:
    """Context holder for current tenant information."""

    def __init__(
        self,
        organization: Organization | None = None,
        membership: Membership | None = None,
    ):
        self.organization = organization
        self.membership = membership

    @property
    def org_id(self) -> UUID | None:
        """Get current organization ID."""
        return self.organization.id if self.organization else None

    @property
    def role(self) -> str | None:
        """Get user's role in current organization."""
        return self.membership.role if self.membership else None

    @property
    def is_admin(self) -> bool:
        """Check if user is admin in current organization."""
        return self.membership.is_admin if self.membership else False

    @property
    def is_owner(self) -> bool:
        """Check if user is owner of current organization."""
        return self.membership.is_owner if self.membership else False


class TenantContextMiddleware(MiddlewareMixin):
    """
    Middleware to set tenant context based on request headers or URL.

    This middleware looks for the organization identifier in:
    1. X-Organization-ID header (UUID)
    2. X-Organization-Slug header (slug)
    3. org_id query parameter

    If found and the user is a member, sets request.tenant with the context.
    """

    def process_request(self, request: HttpRequest) -> None:
        """Process request and set tenant context."""
        request.tenant = TenantContext()

        # Skip if user is not authenticated
        if not hasattr(request, "user") or not request.user.is_authenticated:
            return

        # Try to get organization identifier from various sources
        org_id = self._get_org_id(request)
        org_slug = self._get_org_slug(request)

        if not org_id and not org_slug:
            return

        # Try to get membership
        try:
            if org_id:
                membership = Membership.objects.select_related("organization").get(
                    user=request.user, organization_id=org_id, is_active=True
                )
            else:
                membership = Membership.objects.select_related("organization").get(
                    user=request.user, organization__slug=org_slug, is_active=True
                )

            request.tenant = TenantContext(
                organization=membership.organization,
                membership=membership,
            )

        except Membership.DoesNotExist:
            # User is not a member of this organization
            pass

    def _get_org_id(self, request: HttpRequest) -> UUID | None:
        """Extract organization ID from request."""
        # From header
        org_id = request.headers.get("X-Organization-ID")
        if org_id:
            try:
                return UUID(org_id)
            except ValueError:
                pass

        # From query parameter
        org_id = request.GET.get("org_id")
        if org_id:
            try:
                return UUID(org_id)
            except ValueError:
                pass

        return None

    def _get_org_slug(self, request: HttpRequest) -> str | None:
        """Extract organization slug from request."""
        # From header
        return request.headers.get("X-Organization-Slug")


def get_current_tenant(request: HttpRequest) -> TenantContext:
    """
    Get the current tenant context from request.

    Usage:
        from apps.organizations.middleware import get_current_tenant

        def my_view(request):
            tenant = get_current_tenant(request)
            if tenant.organization:
                # User has a selected organization
                org = tenant.organization
                ...
    """
    return getattr(request, "tenant", TenantContext())


def require_tenant(request: HttpRequest) -> TenantContext:
    """
    Require a tenant context. Raises error if no organization is selected.

    Usage:
        from apps.organizations.middleware import require_tenant

        def my_view(request):
            tenant = require_tenant(request)
            org = tenant.organization
            ...
    """
    from django_matt.core.errors import APIError

    tenant = get_current_tenant(request)
    if not tenant.organization:
        raise APIError(
            status_code=400,
            message="Organization context required. "
            "Set X-Organization-ID or X-Organization-Slug header.",
        )
    return tenant
