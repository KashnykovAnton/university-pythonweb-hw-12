import logging

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Query,
    Request,
    BackgroundTasks,
)
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.services.auth import AuthService, oauth2_scheme
from src.schemas.token import TokenResponse, RefreshTokenRequest
from src.schemas.user import UserResponse, UserCreate
from src.services.email import send_email
from src.services.cache import CacheService, get_cache_service

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger("uvicorn.error")


def get_auth_service(
    db: AsyncSession = Depends(get_db), cache: CacheService = Depends(get_cache_service)
) -> AuthService:
    """
    Dependency function to get an instance of AuthService.

    Args:
        db: AsyncSession from the dependency injection.

    Returns:
        AuthService: An instance of the authentication service.
    """
    return AuthService(db, cache)


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """
    Register a new user account.

    Args:
        user_data: User registration data (username, email, password).
        background_tasks: FastAPI background tasks for sending confirmation email.
        request: The incoming request object.
        auth_service: Injected AuthService instance.

    Returns:
        UserResponse: The newly created user's information.

    Notes:
        - Triggers a background email confirmation task.
        - Validates unique username and email before creation.
        - Passwords are hashed before storage.
    """
    user = await auth_service.register_user(user_data)
    background_tasks.add_task(
        send_email, user.email, user.username, str(request.base_url), "registration"
    )
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """
    Authenticate user and return access/refresh tokens.

    Args:
        form_data: OAuth2 password grant form data (username, password).
        request: The incoming request object (optional).
        auth_service: Injected AuthService instance.

    Returns:
        TokenResponse: Contains access_token and refresh_token.

    Raises:
        HTTPException: 401 if authentication fails.

    Notes:
        - Uses OAuth2 password flow.
        - Records client IP and user-agent for refresh token.
        - Access token has short lifespan, refresh token longer.
    """
    user = await auth_service.authenticate(form_data.username, form_data.password)
    access_token = auth_service.create_access_token(user.username)
    refresh_token = await auth_service.create_refresh_token(
        user.id,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )
    return TokenResponse(
        access_token=access_token, token_type="bearer", refresh_token=refresh_token
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    refresh_token: RefreshTokenRequest,
    request: Request = None,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """
    Refresh an access token using a valid refresh token.

    Args:
        refresh_token: The refresh token request payload.
        request: The incoming request object (optional).
        auth_service: Injected AuthService instance.

    Returns:
        TokenResponse: New access and refresh tokens.

    Raises:
        HTTPException: 401 if refresh token is invalid.

    Notes:
        - Invalidates the old refresh token after use.
        - Generates new tokens with updated metadata.
        - Implements refresh token rotation for security.
    """
    user = await auth_service.validate_refresh_token(refresh_token.refresh_token)

    new_access_token = auth_service.create_access_token(user.username)
    # TODO: Add logic to revoke old access_token and use the new one after the refresh
    new_refresh_token = await auth_service.create_refresh_token(
        user.id,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )

    await auth_service.revoke_refresh_token(refresh_token.refresh_token)

    return TokenResponse(
        access_token=new_access_token,
        token_type="bearer",
        refresh_token=new_refresh_token,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    refresh_token: RefreshTokenRequest,
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> None:
    """
    Invalidate current access and refresh tokens (logout).

    Args:
        refresh_token: The refresh token to invalidate.
        token: The current access token (from Authorization header).
        auth_service: Injected AuthService instance.

    Returns:
        None: HTTP 204 No Content on success.

    Raises:
        HTTPException: 401 if refresh token is invalid or already revoked.

    Notes:
        - Validates that the refresh token is the current active one
        - Adds access token to blacklist until expiration
        - Marks refresh token as revoked in database
        - Effectively terminates current session
    """
    await auth_service.validate_refresh_token(refresh_token.refresh_token)

    await auth_service.revoke_access_token(token)
    await auth_service.revoke_refresh_token(refresh_token.refresh_token)

    return None
