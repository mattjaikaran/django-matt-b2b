"""Authentication API controller."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, make_password

from django_matt.auth import create_token_pair, jwt_required
from django_matt.auth.jwt import refresh_tokens
from django_matt.core import APIController
from django_matt.core.errors import APIError, ValidationAPIError

from ..schemas import (
    ChangePasswordSchema,
    LoginSchema,
    RefreshTokenSchema,
    TokenSchema,
    UserCreateSchema,
    UserSchema,
    UserUpdateSchema,
)

User = get_user_model()


class AuthController(APIController):
    """Authentication controller."""

    tags = ["Auth"]

    @staticmethod
    async def register(request, body: UserCreateSchema) -> UserSchema:
        """Register a new user."""
        # Check if email exists
        if await User.objects.filter(email=body.email).aexists():
            raise ValidationAPIError("Email already registered")

        # Check if username exists
        if await User.objects.filter(username=body.username).aexists():
            raise ValidationAPIError("Username already taken")

        # Create user
        user = await User.objects.acreate(
            email=body.email,
            username=body.username,
            password=make_password(body.password),
            first_name=body.first_name,
            last_name=body.last_name,
        )

        return UserSchema.model_validate(user)

    @staticmethod
    async def login(request, body: LoginSchema) -> TokenSchema:
        """Login and get tokens."""
        try:
            user = await User.objects.aget(email=body.email)
        except User.DoesNotExist:
            raise APIError(status_code=401, message="Invalid credentials")

        if not check_password(body.password, user.password):
            raise APIError(status_code=401, message="Invalid credentials")

        if not user.is_active:
            raise APIError(status_code=401, message="Account is disabled")

        tokens = create_token_pair(user)
        return TokenSchema(**tokens)

    @staticmethod
    async def refresh(request, body: RefreshTokenSchema) -> TokenSchema:
        """Refresh access token."""
        try:
            tokens = refresh_tokens(body.refresh_token)
            return TokenSchema(**tokens)
        except Exception as e:
            raise APIError(status_code=401, message=str(e))

    @staticmethod
    @jwt_required
    async def me(request) -> UserSchema:
        """Get current user profile."""
        return UserSchema.model_validate(request.user)

    @staticmethod
    @jwt_required
    async def update_me(request, body: UserUpdateSchema) -> UserSchema:
        """Update current user profile."""
        user = request.user
        update_data = body.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(user, field, value)

        await user.asave()
        return UserSchema.model_validate(user)

    @staticmethod
    @jwt_required
    async def change_password(request, body: ChangePasswordSchema) -> dict:
        """Change password."""
        user = request.user

        if not check_password(body.current_password, user.password):
            raise ValidationAPIError("Current password is incorrect")

        user.password = make_password(body.new_password)
        await user.asave()

        return {"message": "Password changed successfully"}

    @staticmethod
    @jwt_required
    async def logout(request) -> dict:
        """Logout (client should discard tokens)."""
        # In a stateless JWT system, logout is handled client-side
        # For enhanced security, implement token blacklisting
        return {"message": "Logged out successfully"}
