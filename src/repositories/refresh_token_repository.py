import logging
from datetime import datetime
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import RefreshToken
from src.repositories.base import BaseRepository

logger = logging.getLogger("uvicorn.error")


class RefreshTokenRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        """
        Initialize a RefreshTokenRepository.

        Args:
            session: An asynchronous SQLAlchemy session.
        """
        super().__init__(session, RefreshToken)

    async def get_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        """
        Retrieve a refresh token by its hash.

        Args:
            token_hash: The hashed value of the refresh token.

        Returns:
            A RefreshToken instance if found, otherwise None.
        """
        stmt = select(self.model).where(RefreshToken.token_hash == token_hash)
        token = await self.db.execute(stmt)
        return token.scalars().first()

    async def get_active_token(
        self, token_hash: str, current_time: datetime
    ) -> RefreshToken | None:
        """
        Retrieve an active (not expired or revoked) refresh token by hash.

        Args:
            token_hash: The hashed value of the refresh token.
            current_time: The current datetime for checking expiration.

        Returns:
            An active RefreshToken instance if valid, otherwise None.
        """
        stmt = select(self.model).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.expired_at > current_time,
            RefreshToken.revoked_at.is_(None),
        )
        token = await self.db.execute(stmt)
        return token.scalars().first()

    async def save_token(
        self,
        user_id: int,
        token_hash: str,
        expired_at: datetime,
        ip_address: str,
        user_agent: str,
    ) -> RefreshToken:
        """
        Create and store a new refresh token.

        Args:
            user_id: ID of the user associated with the token.
            token_hash: Hashed token string.
            expired_at: Expiration datetime.
            ip_address: IP address from which the token was issued.
            user_agent: User agent string from the client.

        Returns:
            The newly created RefreshToken instance.
        """
        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expired_at=expired_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return await self.create(refresh_token)

    async def revoke_token(self, refresh_token: RefreshToken) -> None:
        """
        Revoke a refresh token by setting its revoked_at timestamp.

        Args:
            refresh_token: The token instance to revoke.
        """
        refresh_token.revoked_at = datetime.now()
        await self.db.commit()
