# Django Matt B2B

A B2B multi-tenant Django API template built with [django-matt](https://github.com/mattjaikaran/django-matt).

## Features

- Django 6.0+ with full async support
- JWT authentication out of the box
- Multi-tenant organization structure
- Team management with role-based access
- Membership system (owner, admin, member, viewer)
- Invitation system with expiration
- Pydantic schemas for request/response validation
- OpenAPI documentation (Swagger & ReDoc)
- PostgreSQL database
- Docker & Docker Compose
- uv package manager
- Comprehensive testing setup

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager
- PostgreSQL (or use SQLite for development)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/django-matt-b2b.git myproject
cd myproject
```

2. Create and activate virtual environment:
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
make install
# Or: uv pip install -e .
```

4. Copy environment file:
```bash
cp .env.example .env
```

5. Run migrations:
```bash
make migrate
# Or: python manage.py migrate
```

6. Create a superuser:
```bash
make superuser
# Or: python manage.py createsuperuser
```

7. Run the development server:
```bash
make run
# Or: python manage.py runserver
```

### With Docker

```bash
# Start database and cache
make docker-up

# Run migrations
make migrate

# Start development server
make run

# Or run everything in Docker
make docker-up-all
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
- OpenAPI JSON: http://localhost:8000/api/openapi.json

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register a new user |
| POST | `/api/auth/login` | Login and get tokens |
| POST | `/api/auth/refresh` | Refresh access token |
| POST | `/api/auth/logout` | Logout |
| GET | `/api/auth/me` | Get current user |
| PATCH | `/api/auth/me` | Update current user |
| POST | `/api/auth/change-password` | Change password |

### Organizations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/organizations` | List user's organizations |
| POST | `/api/organizations` | Create organization |
| GET | `/api/organizations/{id}` | Get organization |
| PATCH | `/api/organizations/{id}` | Update organization (admin) |
| DELETE | `/api/organizations/{id}` | Delete organization (owner) |
| GET | `/api/organizations/{id}/settings` | Get org settings (admin) |
| PATCH | `/api/organizations/{id}/settings` | Update org settings (admin) |

### Teams

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/organizations/{id}/teams` | List teams |
| POST | `/api/organizations/{id}/teams` | Create team (admin) |
| GET | `/api/organizations/{id}/teams/{tid}` | Get team with members |
| PATCH | `/api/organizations/{id}/teams/{tid}` | Update team (admin) |
| DELETE | `/api/organizations/{id}/teams/{tid}` | Delete team (admin) |
| POST | `/api/organizations/{id}/teams/{tid}/members` | Add member to team |
| DELETE | `/api/organizations/{id}/teams/{tid}/members/{mid}` | Remove from team |

### Members

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/organizations/{id}/members` | List members |
| GET | `/api/organizations/{id}/members/{mid}` | Get member details |
| PATCH | `/api/organizations/{id}/members/{mid}` | Update member (admin) |
| DELETE | `/api/organizations/{id}/members/{mid}` | Remove member (admin) |
| POST | `/api/organizations/{id}/leave` | Leave organization |
| POST | `/api/organizations/{id}/transfer-ownership/{mid}` | Transfer ownership |

### Invitations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/organizations/{id}/invitations` | List invitations (admin) |
| POST | `/api/organizations/{id}/invitations` | Create invitation (admin) |
| POST | `/api/organizations/{id}/invitations/bulk` | Bulk invite (admin) |
| DELETE | `/api/organizations/{id}/invitations/{iid}` | Cancel invitation |
| POST | `/api/organizations/{id}/invitations/{iid}/resend` | Resend invitation |
| GET | `/api/invitations` | Get my invitations |
| POST | `/api/invitations/{token}/accept` | Accept invitation |
| POST | `/api/invitations/{token}/decline` | Decline invitation |

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/ready` | Readiness check (with DB) |

## Project Structure

```
django-matt-b2b/
├── apps/
│   ├── api.py                     # MattAPI initialization
│   ├── core/
│   │   ├── __init__.py
│   │   └── models.py              # Base models (TimestampMixin, etc.)
│   ├── users/
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── controllers.py         # Auth endpoints
│   │   ├── models.py              # User model
│   │   └── schemas.py             # Pydantic schemas
│   └── organizations/
│       ├── __init__.py
│       ├── admin.py
│       ├── apps.py
│       ├── controllers.py         # Org, Team, Member, Invitation endpoints
│       ├── middleware.py          # TenantContextMiddleware
│       ├── models.py              # Organization, Team, Membership, Invitation
│       └── schemas.py             # Pydantic schemas
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_auth.py
│   └── test_organizations.py
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── pyproject.toml
├── manage.py
├── .env.example
├── .gitignore
└── README.md
```

## Roles & Permissions

| Role | Create Team | Manage Members | Manage Settings | Delete Org |
|------|-------------|----------------|-----------------|------------|
| Owner | Yes | Yes | Yes | Yes |
| Admin | Yes | Yes | Yes | No |
| Member | No | No | No | No |
| Viewer | No | No | No | No |

## Multi-tenancy

### Using Tenant Context

Enable the `TenantContextMiddleware` in settings:

```python
MIDDLEWARE = [
    ...
    "apps.organizations.middleware.TenantContextMiddleware",
]
```

Set organization context via headers:
- `X-Organization-ID`: UUID of the organization
- `X-Organization-Slug`: Slug of the organization

Or via query parameter:
- `?org_id=<uuid>`

Access in views:
```python
from apps.organizations.middleware import get_current_tenant, require_tenant

def my_view(request):
    tenant = get_current_tenant(request)
    if tenant.organization:
        # Filter data by organization
        items = Item.objects.filter(organization=tenant.organization)
```

## Development

### Running Tests

```bash
make test
# Or: pytest -v
```

### Linting & Formatting

```bash
make lint    # Run linter
make format  # Format code
```

### Type Generation

Generate TypeScript types for your frontend:

```bash
make sync-types
# Or: python manage.py sync_types --target typescript --output ../frontend/src/types
```

## Deployment

### Environment Variables

See `.env.example` for all available configuration options.

Required for production:
- `SECRET_KEY` - Django secret key
- `DEBUG=False`
- `ALLOWED_HOSTS` - Your domain(s)
- Database credentials

### Docker Deployment

```bash
# Build production image
docker compose build

# Start all services
docker compose up -d
```

## License

MIT
