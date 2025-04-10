from pydantic import BaseModel, EmailStr


class ResetPasswordRequest(BaseModel):
    """
    Schema for password reset request.
    Contains the email address of the user requesting password reset.
    """
    email: EmailStr


class ResetPasswordConfirm(BaseModel):
    """
    Schema for password reset confirmation.
    Contains the new password to be set.
    """
    new_password: str 