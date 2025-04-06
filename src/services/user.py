from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import User
from src.repositories.user_repository import UserRepository
from src.schemas.user import UserCreate
from src.services.auth import AuthService


class UserService:
    """
    Service layer for user management operations.

    This class provides business logic for user-related operations,
    interacting with the UserRepository for database operations
    and AuthService for authentication-related functionality.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize the UserService with database session and dependencies.

        Args:
            db: An AsyncSession object connected to the database.
        """
        self.db = db
        self.user_repository = UserRepository(self.db)
        self.auth_service = AuthService(db)

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

        Note:
            The URL should typically point to an image stored in cloud storage.
        """
        return await self.user_repository.update_avatar_url(email, url)
