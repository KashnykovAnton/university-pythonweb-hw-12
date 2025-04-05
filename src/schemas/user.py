from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict, EmailStr

from src.conf import constants
from src.conf import messages
from src.entity.models import UserRole


class UserBase(BaseModel):
    username: str = Field(
        min_length=constants.USER_NAME_MIN_LENGTH,
        max_length=constants.USER_NAME_MAX_LENGTH,
        description=messages.username_schema.get("ua"),
    )
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(
        min_length=constants.USER_PASSWORD_MIN_LENGTH,
        max_length=constants.USER_PASSWORD_MAX_LENGTH,
        description=messages.password_schema.get("ua"),
    )


class UserResponse(UserBase):
    id: int
    avatar: str | None
    role: UserRole

    model_config = ConfigDict(from_attributes=True)
