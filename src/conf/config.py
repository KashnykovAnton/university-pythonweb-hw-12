import os
from pydantic_settings import BaseSettings
from pydantic import ConfigDict, EmailStr
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """
    Application configuration settings.

    This class defines all environment variables required by the application,
    with type hints and default values from the .env file.

    Configuration is loaded from environment variables with the following precedence:
    1. Actual environment variables
    2. .env file contents
    3. Default values (if specified)
    """

    DB_URL: str = os.getenv("DB_URL")

    # JWT Configuration
    ACCESS_TOKEN_EXPIRE_MINUTES: int = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: int = os.getenv("REFRESH_TOKEN_EXPIRE_DAYS")
    ALGORITHM: str = os.getenv("ALGORITHM")
    SECRET_KEY: str = os.getenv("SECRET_KEY")

    # Redis Configuration
    REDIS_URL: str = os.getenv("REDIS_URL")

    # Email Configuration
    MAIL_USERNAME: EmailStr = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD: str = os.getenv("MAIL_PASSWORD")
    MAIL_FROM: EmailStr = os.getenv("MAIL_FROM")
    MAIL_PORT: int = os.getenv("MAIL_PORT")
    MAIL_SERVER: str = os.getenv("MAIL_SERVER")
    MAIL_FROM_NAME: str = os.getenv("MAIL_FROM_NAME")
    MAIL_STARTTLS: bool = os.getenv("MAIL_STARTTLS")
    MAIL_SSL_TLS: bool = os.getenv("MAIL_SSL_TLS")
    USE_CREDENTIALS: bool = os.getenv("USE_CREDENTIALS")
    VALIDATE_CERTS: bool = os.getenv("VALIDATE_CERTS")

    # Cloudinary Configuration
    CLOUDINARY_NAME: str = os.getenv("CLOUDINARY_NAME")
    CLOUDINARY_API_KEY: str = os.getenv("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET: str = os.getenv("CLOUDINARY_API_SECRET")

    # FastAPI Configuration
    model_config = ConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )
    """
    Pydantic model configuration:
    - Load from .env file with UTF-8 encoding
    - Case sensitive environment variables
    - Ignore extra environment variables not defined here
    """


settings = Settings()
