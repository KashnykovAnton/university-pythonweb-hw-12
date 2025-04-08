from datetime import datetime, timedelta, timezone
import secrets
import hashlib
import jwt
import bcrypt

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from libgravatar import Gravatar
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf.config import settings
from src.conf import messages
from src.entity.models import User
from src.repositories.user_repository import UserRepository
from src.repositories.refresh_token_repository import RefreshTokenRepository
from src.schemas.user import UserCreate, UserResponse
from src.services.cache import CacheService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


class AuthService:
    """
    Service layer for handling authentication and authorization operations.

    This class provides functionality for user registration, authentication,
    token generation and validation, and user management.
    """

    def __init__(self, db: AsyncSession, cache: CacheService):
        """
        Initialize the AuthService with database session and repositories.

        Args:
            db: An AsyncSession object connected to the database.
        """
        self.db = db
        self.user_repository = UserRepository(self.db)
        self.refresh_token_repository = RefreshTokenRepository(self.db)
        self.cache = cache

    def _hash_password(self, password: str) -> str:
        """
        Hash the provided password using bcrypt.

        Args:
            password: The plain-text password to hash.

        Returns:
            The hashed password as a string.
        """
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode(), salt)
        return hashed_password.decode()

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain-text password against its hashed version.

        Args:
            plain_password: The password to verify.
            hashed_password: The stored hashed password to compare against.

        Returns:
            bool: True if passwords match, False otherwise.
        """
        return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

    def _hash_token(self, token: str) -> str:
        """
        Hash a token using SHA-256 for secure storage.

        Args:
            token: The token to hash.

        Returns:
            The hashed token as a hexadecimal string.
        """
        return hashlib.sha256(token.encode()).hexdigest()

    async def authenticate(self, username: str, password: str) -> User:
        """
        Authenticate a user with username and password.

        Args:
            username: The username to authenticate.
            password: The password to verify.

        Returns:
            The authenticated User object if successful.

        Raises:
            HTTPException: If authentication fails due to invalid credentials,
                         unconfirmed email, or non-existent user.
        """
        cached_user = await self.cache.get_cached_user(username)
        if cached_user:
            return cached_user

        user = await self.user_repository.get_by_username(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=messages.authenticate_wrong_user.get("ua"),
            )
        if not user.confirmed:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=messages.authentificate_email_not_confirmed.get("ua"),
            )
        if not self._verify_password(password, user.hash_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=messages.authenticate_wrong_user.get("ua"),
            )
        await self.cache.cache_user(user)
        return user

    async def register_user(self, user_data: UserCreate) -> User:
        """
        Register a new user in the system.

        Args:
            user_data: UserCreate schema containing registration details.

        Returns:
            The newly created User object.

        Raises:
            HTTPException: If username or email already exists in the system.
        """
        if await self.user_repository.get_by_username(user_data.username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=messages.user_exists.get("ua"),
            )
        if await self.user_repository.get_user_by_email(str(user_data.email)):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=messages.mail_exists.get("ua"),
            )

        avatar = None
        try:
            g = Gravatar(user_data.email)
            avatar = g.get_image()
        except Exception as e:
            print(f"Gravatar error: {e}")

        hashed_password = self._hash_password(user_data.password)
        user = await self.user_repository.create_user(
            user_data, hashed_password, avatar
        )
        return user

    def create_access_token(self, username: str) -> str:
        """
        Generate a JWT access token for the specified user.

        Args:
            username: The username to include in the token.

        Returns:
            The encoded JWT access token as a string.
        """
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        expire = datetime.now(timezone.utc) + expires_delta

        to_encode = {"sub": username, "exp": expire}
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )

        return encoded_jwt

    async def create_refresh_token(
        self, user_id: int, ip_address: str | None, user_agent: str | None
    ) -> str:
        """
        Generate and store a refresh token for the specified user.

        Args:
            user_id: The ID of the user to create the token for.
            ip_address: The IP address from which the request originated.
            user_agent: The user agent string from the client.

        Returns:
            The newly generated refresh token as a URL-safe string.
        """
        token = secrets.token_urlsafe(32)
        token_hash = self._hash_token(token)
        expired_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        await self.refresh_token_repository.save_token(
            user_id, token_hash, expired_at, ip_address, user_agent
        )
        return token

    def decode_and_validate_access_token(self, token: str) -> dict:
        """
        Decode and validate a JWT access token.

        Args:
            token: The JWT token to decode and validate.

        Returns:
            The decoded token payload as a dictionary.

        Raises:
            HTTPException: If the token is invalid or expired.
        """
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            return payload
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=messages.invalid_token.get("ua"),
            )

    async def get_current_user(self, token: str = Depends(oauth2_scheme)) -> User:
        """
        Retrieve the current authenticated user from the access token.

        Args:
            token: The JWT access token.

        Returns:
            The authenticated User object.

        Raises:
            HTTPException: If the token is revoked, invalid, or user not found.
        """

        if await self.cache.is_token_revoked(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=messages.revoked_token.get("ua"),
            )

        payload = self.decode_and_validate_access_token(token)
        username = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=messages.validate_credentials.get("ua"),
            )

        cached_user = await self.cache.get_cached_user(username)
        if cached_user:
            return cached_user

        user = await self.user_repository.get_by_username(username)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=messages.validate_credentials.get("ua"),
            )

        await self.cache.cache_user(user)
        return user

    async def validate_refresh_token(self, token: str) -> User:
        """
        Validate a refresh token and return its associated user.

        Args:
            token: The refresh token to validate.

        Returns:
            The User associated with the valid refresh token.

        Raises:
            HTTPException: If the token is invalid, expired, or user not found.
        """
        token_hash = self._hash_token(token)
        current_time = datetime.now(timezone.utc)
        refresh_token = await self.refresh_token_repository.get_active_token(
            token_hash, current_time
        )

        if refresh_token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=messages.invalid_refresh_token.get("ua"),
            )

        user = await self.user_repository.get_by_id(refresh_token.user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=messages.invalid_refresh_token.get("ua"),
            )
        return user

    async def revoke_refresh_token(self, token: str) -> None:
        """
        Revoke a refresh token by marking it as revoked.

        Args:
            token: The refresh token to revoke.
        """
        token_hash = self._hash_token(token)
        current_time = datetime.now(timezone.utc)
        refresh_token = await self.refresh_token_repository.get_active_token(
            token_hash, current_time
        )
        if refresh_token:
            await self.refresh_token_repository.revoke_token(refresh_token)
        return None

    async def revoke_access_token(self, token: str) -> None:
        """
        Revoke an access token by adding it to the blacklist.

        Args:
            token: The access token to revoke.
        """
        payload = self.decode_and_validate_access_token(token)
        exp = payload.get("exp")
        if exp:
            expire_at = datetime.fromtimestamp(exp, timezone.utc)
            await self.cache.revoke_token(token, expire_at)
        return None
