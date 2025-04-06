from pydantic import BaseModel


class TokenResponse(BaseModel):
    """
    Schema for JWT token response.

    Contains both access and refresh tokens with their type.
    Returned after successful authentication or token refresh.
    """

    access_token: str
    token_type: str = "bearer"
    refresh_token: str


class RefreshTokenRequest(BaseModel):
    """
    Schema for refresh token requests.

    Used when submitting a refresh token to obtain new access tokens.
    """

    refresh_token: str
