"""User API controllers."""

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, make_password

from django_matt import MattAPI
from django_matt.auth import create_token_pair, jwt_required, refresh_access_token
from django_matt.core import APIController
from django_matt.core.errors import APIError, NotFoundAPIError, ValidationAPIError

from .schemas import (
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
    async def register(request, data: UserCreateSchema) -> UserSchema:
        """Register a new user."""
        # Check if email exists
        if await User.objects.filter(email=data.email).aexists():
            raise ValidationAPIError("Email already registered")

        # Check if username exists
        if await User.objects.filter(username=data.username).aexists():
            raise ValidationAPIError("Username already taken")

        # Create user
        user = await User.objects.acreate(
            email=data.email,
            username=data.username,
            password=make_password(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
        )

        return UserSchema.model_validate(user)

    @staticmethod
    async def login(request, data: LoginSchema) -> TokenSchema:
        """Login and get tokens."""
        try:
            user = await User.objects.aget(email=data.email)
        except User.DoesNotExist:
            raise APIError(status_code=401, message="Invalid credentials")

        if not check_password(data.password, user.password):
            raise APIError(status_code=401, message="Invalid credentials")

        if not user.is_active:
            raise APIError(status_code=401, message="Account is disabled")

        tokens = create_token_pair(user)
        return TokenSchema(**tokens)

    @staticmethod
    async def refresh(request, data: RefreshTokenSchema) -> TokenSchema:
        """Refresh access token."""
        try:
            tokens = refresh_access_token(data.refresh_token)
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
    async def update_me(request, data: UserUpdateSchema) -> UserSchema:
        """Update current user profile."""
        user = request.user
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(user, field, value)

        await user.asave()
        return UserSchema.model_validate(user)

    @staticmethod
    @jwt_required
    async def change_password(request, data: ChangePasswordSchema) -> dict:
        """Change password."""
        user = request.user

        if not check_password(data.current_password, user.password):
            raise ValidationAPIError("Current password is incorrect")

        user.password = make_password(data.new_password)
        await user.asave()

        return {"message": "Password changed successfully"}

    @staticmethod
    @jwt_required
    async def logout(request) -> dict:
        """Logout (client should discard tokens)."""
        # In a stateless JWT system, logout is handled client-side
        # For enhanced security, implement token blacklisting
        return {"message": "Logged out successfully"}


def register_auth_routes(api: MattAPI) -> None:
    """Register auth routes on the API."""
    api.post("/auth/register", response=UserSchema, tags=["Auth"])(AuthController.register)
    api.post("/auth/login", response=TokenSchema, tags=["Auth"])(AuthController.login)
    api.post("/auth/refresh", response=TokenSchema, tags=["Auth"])(AuthController.refresh)
    api.post("/auth/logout", tags=["Auth"])(AuthController.logout)
    api.get("/auth/me", response=UserSchema, tags=["Auth"])(AuthController.me)
    api.patch("/auth/me", response=UserSchema, tags=["Auth"])(AuthController.update_me)
    api.post("/auth/change-password", tags=["Auth"])(AuthController.change_password)
