from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.entity.models import User, UserRole
from src.services.auth import AuthService, oauth2_scheme
from src.services.user import UserService
from src.conf import messages


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """
    Dependency function that provides an AuthService instance.

    Args:
        db: AsyncSession from the dependency injection.

    Returns:
        AuthService: An instance of the authentication service.
    """
    return AuthService(db)


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """
    Dependency function that provides a UserService instance.

    Args:
        db: AsyncSession from the dependency injection.

    Returns:
        UserService: An instance of the user service.
    """
    return UserService(db)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    """
    Dependency function that retrieves the current authenticated user.

    Args:
        token: JWT access token from the Authorization header.
        auth_service: Injected AuthService instance.

    Returns:
        User: The authenticated user object.

    Raises:
        HTTPException: 401 if token is invalid or user not found.
    """
    return await auth_service.get_current_user(token)


def get_current_moderator_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency function that verifies moderator-level access.

    Args:
        current_user: Authenticated user from dependency injection.

    Returns:
        User: The authenticated user if they have moderator privileges.

    Raises:
        HTTPException: 403 if user doesn't have moderator or admin role.
    """
    if current_user.role not in [UserRole.MODERATOR, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail=messages.role_access_info.get("ua"))
    return current_user


def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency function that verifies admin-level access.

    Args:
        current_user: Authenticated user from dependency injection.

    Returns:
        User: The authenticated user if they have admin privileges.

    Raises:
        HTTPException: 403 if user doesn't have admin role.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail=messages.role_access_info.get("ua"))
    return current_user
