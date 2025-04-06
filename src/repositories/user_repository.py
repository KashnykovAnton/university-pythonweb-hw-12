import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import User
from src.repositories.base import BaseRepository
from src.schemas.user import UserCreate

logger = logging.getLogger("uvicorn.error")


class UserRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        """
        Initialize a UserRepository.

        Args:
            session: An asynchronous SQLAlchemy session.
        """
        super().__init__(session, User)

    async def get_by_username(self, username: str) -> User | None:
        """
        Retrieve a user by username.

        Args:
            username: The username of the user.

        Returns:
            A User instance if found, otherwise None.
        """
        stmt = select(self.model).where(User.username == username)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        """
        Retrieve a user by email address.

        Args:
            email: The email of the user.

        Returns:
            A User instance if found, otherwise None.
        """
        stmt = select(self.model).where(User.email == email)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def create_user(
        self, user_data: UserCreate, hashed_password: str, avatar: str
    ) -> User:
        """
        Create a new user in the database.

        Args:
            user_data: Schema with user registration data.
            hashed_password: The hashed password to store.
            avatar: URL or path to the user's avatar.

        Returns:
            The created User instance.
        """
        user = User(
            **user_data.model_dump(exclude_unset=True, exclude={"password"}),
            hash_password=hashed_password,
            avatar=avatar,
        )
        return await self.create(user)

    async def confirmed_email(self, email: str) -> None:
        """
        Mark a user's email as confirmed.

        Args:
            email: The email address of the user.
        """
        user = await self.get_user_by_email(email)
        user.confirmed = True
        await self.db.commit()

    async def update_avatar_url(self, email: str, url: str) -> User:
        """
        Update the user's avatar URL.

        Args:
            email: The email address of the user.
            url: The new avatar URL.

        Returns:
            The updated User instance.
        """
        user = await self.get_user_by_email(email)
        user.avatar = url
        await self.db.commit()
        await self.db.refresh(user)
        return user
