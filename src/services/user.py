import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import Depends, HTTPException, status
from src.entity.models import User, UserRole
from src.repositories.user_repository import UserRepository
from src.schemas.user import UserCreate
from src.services.auth import AuthService
from src.conf.config import settings
from src.schemas.user import UserResponse
from src.services.cache import CacheService
from src.conf import messages
from src.core.email_token import get_email_from_token


class UserService:
    """
    Service layer for user management operations.

    This class provides business logic for user-related operations,
    interacting with the UserRepository for database operations
    and AuthService for authentication-related functionality.
    """

    def __init__(self, db: AsyncSession, cache_service: CacheService):
        """
        Initialize the UserService with database session and dependencies.

        Args:
            db: An AsyncSession object connected to the database.
        """
        self.db = db
        self.user_repository = UserRepository(self.db)
        self.auth_service = AuthService(db, cache_service)
        self.cache_service = cache_service

    async def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user in the system.

        Args:
            user_data: UserCreate schema containing user registration details.

        Returns:
            The newly created User object.

        Note:
            Delegates to AuthService.register_user which handles:
            - Password hashing
            - Email uniqueness validation
            - Username uniqueness validation
            - Gravatar avatar generation
        """
        user = await self.auth_service.register_user(user_data)
        return user

    async def get_user_by_username(self, username: str) -> User | None:
        """
        Retrieve a user by their username.

        Args:
            username: The username to search for.

        Returns:
            The User object if found, None otherwise.
        """
        user = await self.user_repository.get_by_username(username)
        return user

    async def get_user_by_email(self, email: str) -> User | None:
        """
        Retrieve a user by their email address.

        Args:
            email: The email address to search for.

        Returns:
            The User object if found, None otherwise.
        """
        user = await self.user_repository.get_user_by_email(email)
        return user

    async def confirmed_email(self, email: str) -> None:
        """
        Mark a user's email as confirmed in the system.

        Args:
            email: The email address of the user to confirm.

        Returns:
            None: This method performs an update but doesn't return a value.

        Note:
            Typically called after a user successfully verifies their email.
        """
        user = await self.user_repository.confirmed_email(email)
        return user

    async def update_avatar_url(self, email: str, url: str) -> User:
        """
        Update a user's avatar URL.

        Args:
            email: The email address of the user to update.
            url: The new avatar URL to set.

        Returns:
            The updated User object.

        Raises:
            HTTPException: 403 if user doesn't have admin role.
            HTTPException: 404 if user not found.

        Note:
            Only users with ADMIN role can update their avatar.
        """
        user = await self.user_repository.get_user_by_email(email)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=messages.contact_not_found.get("ua"),
            )

        if user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=messages.role_access_info.get("ua"),
            )

        user = await self.user_repository.update_avatar_url(email, url)

        await self.cache_service.delete_user_cache(user.username)
        await self.cache_service.cache_user(user)

        return user

    async def request_password_reset(self, email: str) -> User:
        """
        Initiate password reset process by sending reset email.

        Args:
            email: The email address of the user requesting password reset.

        Raises:
            HTTPException: If user with given email doesn't exist.
        """
        user = await self.get_user_by_email(email)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=messages.contact_not_found.get("ua"),
            )
        return user

    async def reset_password(self, token: str, new_password: str) -> None:
        """
        Reset user's password using the provided token.

        Args:
            token: The password reset token.
            new_password: The new password to set.

        Raises:
            HTTPException: If token is invalid or expired.
        """
        try:
            email = get_email_from_token(token)
            user = await self.user_repository.get_user_by_email(email)

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=messages.contact_not_found.get("ua"),
                )

            hashed_password = self.auth_service._hash_password(new_password)
            await self.user_repository.update_password(email, hashed_password)

            await self.cache_service.delete_user_cache(user.username)
            await self.cache_service.cache_user(user)

        except HTTPException:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=messages.invalid_email_token.get("ua"),
            )