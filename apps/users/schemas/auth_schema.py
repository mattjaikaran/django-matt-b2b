"""Authentication Pydantic schemas."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


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
