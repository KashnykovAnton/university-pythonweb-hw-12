import redis.asyncio as redis
from datetime import datetime, timezone
from src.conf.config import settings
from src.entity.models import User
from src.schemas.user import UserResponse


class CacheService:
    """Service for managing Redis cache operations.

    Handles all Redis interactions including:
    - Token blacklisting
    - User data caching
    - Cache invalidation

    Args:
        redis_url: Redis connection URL from settings
        cache_ttl: Default time-to-live for cached items in seconds
    """

    def __init__(self):
        """Initialize Redis client with application settings."""
        self.redis = redis.from_url(settings.REDIS_URL)
        self.cache_ttl = settings.REDIS_TTL

    async def is_token_revoked(self, token: str) -> bool:
        """Check if a token has been revoked.

        Args:
            token: JWT access token to check

        Returns:
            bool: True if token is revoked, False otherwise
        """
        result = await self.redis.exists(f"black-list:{token}")
        return bool(result)

    async def revoke_token(self, token: str, expire_at: datetime) -> None:
        """Add a token to the revocation blacklist.

        Args:
            token: JWT access token to revoke
            expire_at: Datetime when token expires

        Note:
            The token will be automatically removed from blacklist upon expiration.
        """
        if expire_at > datetime.now(timezone.utc):
            ttl = int((expire_at - datetime.now(timezone.utc)).total_seconds())
            await self.redis.setex(f"black-list:{token}", ttl, "1")

    async def get_cached_user(self, username: str) -> User | None:
        """Retrieve a user from cache.

        Args:
            username: Username to lookup in cache

        Returns:
            User: The cached User object if found
            None: If user not in cache

        Note:
            Automatically converts cached JSON to SQLAlchemy User model
        """
        cached_user = await self.redis.get(f"user:{username}")
        if cached_user:
            user_data = UserResponse.model_validate_json(cached_user)
            return User(**user_data.model_dump())
        return None

    async def cache_user(self, user: User) -> None:
        """Store user data in cache.

        Args:
            user: User object to cache

        Note:
            Uses UserResponse schema for serialization
            Applies configured TTL to cached data
        """
        user_data = UserResponse.from_orm(user)
        await self.redis.setex(
            f"user:{user.username}", self.cache_ttl, user_data.model_dump_json()
        )

    async def delete_user_cache(self, username: str) -> None:
        """Remove user data from cache.

        Args:
            username: Username to remove from cache

        Note:
            Typically called when user data is updated
        """
        await self.redis.delete(f"user:{username}")


cache_service = CacheService()


async def get_cache_service() -> CacheService:
    """Dependency function to get CacheService instance.

    Returns:
        CacheService: The shared cache service instance
    """
    return cache_service
