"""
Authentication router — provides user registration and login endpoints.

Mounts under ``/api/auth`` via main.py include_router with prefix="/api".

Endpoints:
    POST /auth/register — create a new user account
    POST /auth/login    — authenticate and receive JWT access token

The login endpoint uses OAuth2PasswordRequestForm so that the Swagger
"Authorize" button works out of the box.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.auth import (
    RegisterResponse,
    TokenResponse,
    UserRegister,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ---------------------------------------------------------------------------
# POST /auth/register
# ---------------------------------------------------------------------------

@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description=(
        "Creates a new user account and returns an access token "
        "for immediate authentication. Default role is 'staff'."
    ),
)
async def register(
    schema: UserRegister,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    try:
        user, token = await service.register(schema)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return RegisterResponse(
        user=UserResponse.model_validate(user),
        access_token=token,
    )


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and obtain access token",
    description=(
        "Authenticate with email + password. Returns a JWT bearer token. "
        "Use the Swagger 'Authorize' button — the form sends credentials "
        "as OAuth2 form data automatically."
    ),
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """
    Accepts OAuth2PasswordRequestForm so Swagger's Authorize dialog works.
    form_data.username = email, form_data.password = password.
    """
    service = AuthService(db)
    try:
        _user, token = await service.login(
            # Map OAuth2 form fields → our UserLogin-like interface
            type(
                "LoginPayload",
                (),
                {"username": form_data.username, "password": form_data.password},
            )()
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(access_token=token)
