from __future__ import annotations

import jwt
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User, UserRole

# OAuth2 scheme for extracting Bearer token from authorization header
# We configure tokenUrl as 'api/auth/login' (or whatever authentication login endpoint will be)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """FastAPI dependency to retrieve the currently authenticated user.
    
    Validates the JWT access token and fetches the user from the database.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    try:
        # Decode and validate signature/expiration
        payload = decode_token(token)
        
        # Validate that the token is an access token, not a refresh token
        token_type = payload.get("type")
        if token_type != "access":
            raise credentials_exception
            
        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
            
        try:
            user_id = UUID(user_id_str)
        except ValueError:
            raise credentials_exception
            
    except jwt.PyJWTError:
        raise credentials_exception

    # Query the user using SQLAlchemy 2.0 Async Select
    # Only fetch users who are not soft-deleted
    query = select(User).where(User.id == user_id, User.is_deleted == False)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
        
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Dependency that ensures the authenticated user is active.
    
    Since soft-deleted users are already filtered out in get_current_user,
    this returns the user directly, but provides a hook for future status checks.
    """
    return current_user


def require_role(allowed_roles: list[UserRole | str]):
    """Dynamic role requirement dependency creator.
    
    Example:
        current_user: User = Depends(require_role(["admin", "hr"]))
    """
    async def role_checker(
        current_user: User = Depends(get_current_user)
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: requires one of the roles: {allowed_roles}"
            )
        return current_user
    return role_checker


# Static helper for requiring admin role directly
require_admin = require_role([UserRole.ADMIN])
