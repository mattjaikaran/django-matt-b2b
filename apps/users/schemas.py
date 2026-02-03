"""Pydantic schemas for user endpoints."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserSchema(BaseModel):
    """User response schema."""

    id: int
    email: EmailStr
    username: str
    first_name: str = ""
    last_name: str = ""
    avatar_url: str | None = None
    bio: str = ""
    phone: str = ""
    timezone: str = "UTC"
    locale: str = "en"
    is_active: bool = True
    date_joined: datetime

    class Config:
        from_attributes = True


class UserCreateSchema(BaseModel):
    """User registration schema."""

    email: EmailStr
    username: str = Field(..., min_length=3, max_length=150)
    password: str = Field(..., min_length=8)
    first_name: str = ""
    last_name: str = ""


class UserUpdateSchema(BaseModel):
    """User update schema."""

    first_name: str | None = None
    last_name: str | None = None
    avatar_url: str | None = None
    bio: str | None = None
    phone: str | None = None
    timezone: str | None = None
    locale: str | None = None


class ChangePasswordSchema(BaseModel):
    """Change password schema."""

    current_password: str
    new_password: str = Field(..., min_length=8)


class LoginSchema(BaseModel):
    """Login request schema."""

    email: EmailStr
    password: str


class TokenSchema(BaseModel):
    """Token response schema."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenSchema(BaseModel):
    """Refresh token request schema."""

    refresh_token: str


class UserSummarySchema(BaseModel):
    """Minimal user info for embedding in other responses."""

    id: int
    email: EmailStr
    username: str
    first_name: str = ""
    last_name: str = ""
    avatar_url: str | None = None

    class Config:
        from_attributes = True
