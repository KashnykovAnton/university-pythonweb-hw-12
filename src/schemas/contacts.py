from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from src.conf import constants
from src.conf import messages


class ContactSchema(BaseModel):
    """
    Pydantic schema for creating a new contact.

    This schema defines the structure and validation rules for contact creation.
    All fields are required unless otherwise specified.
    """

    first_name: str = Field(
        min_length=constants.NAME_MIN_LENGTH,
        max_length=constants.NAME_MAX_LENGTH,
        description=messages.contact_schema_first_name.get("ua"),
    )
    last_name: str = Field(
        min_length=constants.NAME_MIN_LENGTH,
        max_length=constants.NAME_MAX_LENGTH,
        description=messages.contact_schema_last_name.get("ua"),
    )
    email: EmailStr = Field(
        min_length=constants.EMAIL_MIN_LENGTH,
        max_length=constants.EMAIL_MAX_LENGTH,
        description=messages.contact_schema_email.get("ua"),
    )
    phone_number: str = Field(
        min_length=constants.PHONE_MIN_LENGTH,
        max_length=constants.PHONE_MAX_LENGTH,
        description=messages.contact_schema_phone_number.get("ua"),
    )
    birthday: date = Field(description=messages.contact_schema_birthday.get("ua"))
    additional_info: Optional[str] = Field(
        default=None,
        max_length=constants.ADDITIONAL_INFO_MAX_LENGTH,
        description=messages.contact_schema_additional_info.get("ua"),
    )


class ContactUpdateSchema(BaseModel):
    """
    Pydantic schema for updating an existing contact.

    This schema defines the structure and validation rules for contact updates.
    All fields are optional - only provided fields will be updated.
    """

    first_name: Optional[str] = Field(
        default=None,
        min_length=constants.NAME_MIN_LENGTH,
        max_length=constants.NAME_MAX_LENGTH,
        description=messages.contact_schema_first_name.get("ua"),
    )
    last_name: Optional[str] = Field(
        default=None,
        min_length=constants.NAME_MIN_LENGTH,
        max_length=constants.NAME_MAX_LENGTH,
        description=messages.contact_schema_last_name.get("ua"),
    )
    email: Optional[EmailStr] = Field(
        default=None,
        min_length=constants.EMAIL_MIN_LENGTH,
        max_length=constants.EMAIL_MAX_LENGTH,
        description=messages.contact_schema_email.get("ua"),
    )
    phone_number: Optional[str] = Field(
        default=None,
        min_length=constants.PHONE_MIN_LENGTH,
        max_length=constants.PHONE_MAX_LENGTH,
        description=messages.contact_schema_phone_number.get("ua"),
    )
    birthday: Optional[date] = Field(
        default=None, description=messages.contact_schema_birthday.get("ua")
    )
    additional_info: Optional[str] = Field(
        default=None,
        max_length=constants.ADDITIONAL_INFO_MAX_LENGTH,
        description=messages.contact_schema_additional_info.get("ua"),
    )


class ContactResponse(BaseModel):
    """
    Pydantic schema for contact response data.

    This schema defines how contact data is returned from the API,
    including all fields and timestamps.
    """

    id: int
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    birthday: date
    additional_info: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
