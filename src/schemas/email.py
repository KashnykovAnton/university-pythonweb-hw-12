from pydantic import BaseModel, EmailStr


class RequestEmail(BaseModel):
    """
    Schema for email request operations.

    Used when an operation requires only an email address as input,
    such as requesting email confirmation or password reset.
    """

    email: EmailStr
