from datetime import datetime
from enum import Enum

from sqlalchemy import (
    String,
    DateTime,
    Date,
    func,
    text,
    ForeignKey,
    Text,
    Enum as SqlEnum,
    Boolean,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from src.conf import constants


class Base(DeclarativeBase):
    """
    Base class for declarative SQLAlchemy models.

    The metadata attribute contains:
    - Table collection
    - Schema management
    - Migration support

    See SQLAlchemy's `DeclarativeBase.metadata` documentation for details.
    """

    pass


class Contact(Base):
    """
    SQLAlchemy model for storing contact information.

    Attributes:
        id: The unique identifier for the contact.
        first_name: The first name of the contact.
        last_name: The last name of the contact.
        email: The email address of the contact.
        phone_number: The phone number of the contact.
        birthday: The birth date of the contact.
        additional_info: Optional additional notes or information.
        created_at: Timestamp when the contact was created.
        updated_at: Timestamp when the contact was last updated.
        user_id: The ID of the user who owns the contact.
        user: Relationship to the user who owns this contact.
    """

    __tablename__ = "contacts"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    first_name: Mapped[str] = mapped_column(
        String(constants.NAME_MAX_LENGTH), nullable=False
    )
    last_name: Mapped[str] = mapped_column(
        String(constants.NAME_MAX_LENGTH), nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(constants.EMAIL_MAX_LENGTH), unique=True, nullable=False
    )
    phone_number: Mapped[str] = mapped_column(
        String(constants.PHONE_MAX_LENGTH), nullable=False
    )
    birthday: Mapped[datetime] = mapped_column(Date, nullable=False)
    additional_info: Mapped[str] = mapped_column(
        String(constants.ADDITIONAL_INFO_MAX_LENGTH), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    user: Mapped["User"] = relationship("User", backref="contacts", lazy="joined")


class UserRole(str, Enum):
    """
    Enumeration for user roles.

    Values:
        USER: Regular user.
        MODERATOR: User with moderation privileges.
        ADMIN: User with administrative privileges.
    """

    USER = constants.ROLE_USER
    MODERATOR = constants.ROLE_MODERATOR
    ADMIN = constants.ROLE_ADMIN


class User(Base):
    """
    SQLAlchemy model for storing user account information.

    Attributes:
        id: The unique identifier for the user.
        username: The user's unique username.
        email: The user's unique email address.
        hash_password: The hashed password for authentication.
        role: The user's role (user, moderator, or admin).
        avatar: Optional URL to the user's avatar image.
        confirmed: Indicates whether the user's email is confirmed.
        refresh_tokens: Relationship to refresh tokens for the user.
    """

    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(nullable=False, unique=True)
    email: Mapped[str] = mapped_column(nullable=False, unique=True)
    hash_password: Mapped[str] = mapped_column(nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SqlEnum(UserRole), default=UserRole.USER, nullable=False
    )
    avatar: Mapped[str] = mapped_column(String(255), nullable=True)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="user"
    )


class RefreshToken(Base):
    """
    SQLAlchemy model for storing refresh token metadata.

    Attributes:
        id: The unique identifier for the refresh token.
        user_id: The ID of the associated user.
        token_hash: The hashed value of the refresh token.
        created_at: Timestamp of when the token was created.
        expired_at: Timestamp of token expiration.
        revoked_at: Optional timestamp if the token was revoked.
        ip_address: Optional IP address where the token was issued.
        user_agent: Optional user agent string from the client.
        user: Relationship to the user who owns the token.
    """

    __tablename__ = "refresh_tokens"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    expired_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    revoked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    ip_address: Mapped[str] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[str] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")
