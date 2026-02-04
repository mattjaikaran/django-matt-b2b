"""Route registration for user controllers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..schemas import TokenSchema, UserSchema
from .auth_controller import AuthController

if TYPE_CHECKING:
    from django_matt import MattAPI


def register_auth_routes(api: MattAPI) -> None:
    """Register auth routes on the API."""
    api.post("auth/register", response_model=UserSchema, tags=["Auth"])(AuthController.register)
    api.post("auth/login", response_model=TokenSchema, tags=["Auth"])(AuthController.login)
    api.post("auth/refresh", response_model=TokenSchema, tags=["Auth"])(AuthController.refresh)
    api.post("auth/logout", tags=["Auth"])(AuthController.logout)
    api.get("auth/me", response_model=UserSchema, tags=["Auth"])(AuthController.me)
    api.patch("auth/me", response_model=UserSchema, tags=["Auth"])(AuthController.update_me)
    api.post("auth/change-password", tags=["Auth"])(AuthController.change_password)
