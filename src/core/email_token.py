from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, status

from src.conf.config import settings
from src.conf import messages


def create_email_token(data: dict) -> str:
    """
    Create a JWT token for email verification purposes.

    Args:
        data: Dictionary containing the payload data (must include 'sub' key with email).

    Returns:
        str: A JWT token string with 7-day expiration.

    Notes:
        - The token includes standard JWT claims (iat, exp) in addition to provided data.
        - Uses application secret key and algorithm from settings.
        - Default expiration is 7 days from creation.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode.update({"iat": datetime.now(timezone.utc), "exp": expire})
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


def get_email_from_token(token: str) -> str:
    """
    Extract email address from a JWT verification token.

    Args:
        token: JWT token string to decode.

    Returns:
        str: The email address extracted from the token's 'sub' claim.

    Raises:
        HTTPException: 422 if token is invalid, expired, or doesn't contain email.

    Notes:
        - Validates token signature using application secret key.
        - Checks token expiration.
        - Requires 'sub' claim containing the email address.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email = payload["sub"]
        return email
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=messages.invalid_email_token.get("ua"),
        )
