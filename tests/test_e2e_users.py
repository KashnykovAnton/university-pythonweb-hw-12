import pytest
from unittest.mock import patch

from tests.conftest import test_user, TestingSessionLocal
from src.entity.models import User, UserRole
from src.services.auth import AuthService
from tests.conftest import FakeCacheService
from src.core.email_token import create_email_token


@pytest.fixture
async def regular_user():
    async with TestingSessionLocal() as session:
        regular_user = User(
            username="regular_user",
            email="regular@example.com",
            hash_password="hashed_password",
            role=UserRole.USER,
            confirmed=True
        )
        session.add(regular_user)
        await session.commit()
        return regular_user


@pytest.fixture
async def regular_user_token(regular_user):
    user = await regular_user
    async with TestingSessionLocal() as session:
        auth_service = AuthService(session, FakeCacheService())
        token = auth_service.create_access_token(user.username)
        return token


def test_get_me(client, get_token):
    with patch("src.services.cache.CacheService.is_token_revoked") as mock_is_revoked:
        mock_is_revoked.return_value = False
        token = get_token
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/users/me", headers=headers)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["username"] == test_user["username"]
        assert data["email"] == test_user["email"]
        assert "avatar" in data


@patch("src.services.upload_file_service.UploadFileService.upload_file")
def test_update_avatar_user(mock_upload_file, client, get_token):
    with patch("src.services.cache.CacheService.is_token_revoked") as mock_is_revoked:
        mock_is_revoked.return_value = False
        fake_url = "http://example.com/avatar.jpg"
        mock_upload_file.return_value = fake_url

        headers = {"Authorization": f"Bearer {get_token}"}

        file_data = {"file": ("avatar.jpg", b"fake image content", "image/jpeg")}

        response = client.patch("/api/users/avatar", headers=headers, files=file_data)

        assert response.status_code == 200, response.text

        data = response.json()
        assert data["username"] == test_user["username"]
        assert data["email"] == test_user["email"]
        assert data["avatar"] == fake_url

        mock_upload_file.assert_called_once()


@pytest.mark.asyncio
async def test_get_moderator_endpoint(client, regular_user_token):
    token = await regular_user_token
    with patch("src.services.cache.CacheService.is_token_revoked") as mock_is_revoked:
        mock_is_revoked.return_value = False
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/users/moderator", headers=headers)
        assert response.status_code == 403, response.text
        assert response.json()["detail"] == "Недостатньо прав доступу"


@pytest.fixture
async def admin_regular_user():
    async with TestingSessionLocal() as session:
        admin_regular_user = User(
            username="admin_regular_user",
            email="admin_regular@example.com",
            hash_password="hashed_password",
            role=UserRole.USER,
            confirmed=True
        )
        session.add(admin_regular_user)
        await session.commit()
        return admin_regular_user


@pytest.fixture
async def admin_regular_user_token(admin_regular_user):
    user = await admin_regular_user
    async with TestingSessionLocal() as session:
        auth_service = AuthService(session, FakeCacheService())
        token = auth_service.create_access_token(user.username)
        return token


@pytest.mark.asyncio
async def test_get_admin_endpoint(client, admin_regular_user_token):
    token = await admin_regular_user_token
    with patch("src.services.cache.CacheService.is_token_revoked") as mock_is_revoked:
        mock_is_revoked.return_value = False
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/users/admin", headers=headers)
        assert response.status_code == 403, response.text
        assert response.json()["detail"] == "Недостатньо прав доступу"


@patch("src.services.user.UserService.request_password_reset")
def test_request_password_reset(mock_request_reset, client):
    mock_request_reset.return_value = None
    response = client.post(
        "/api/users/reset_password_request",
        json={"email": test_user["email"]}
    )
    assert response.status_code == 200, response.text
    assert response.json()["message"] == "Password reset email has been sent"
    mock_request_reset.assert_called_once()


@patch("src.services.user.UserService.reset_password")
@pytest.mark.asyncio
async def test_reset_password(mock_reset_password, client):
    mock_reset_password.return_value = None
    response = client.post(
        "/api/users/reset_password_request",
        json={"email": test_user["email"]}
    )
    assert response.status_code == 200

    token = create_email_token({"sub": test_user["email"]})
    
    response = client.post(
        f"/api/users/reset_password/{token}",
        json={"new_password": "newpassword123"}
    )
    assert response.status_code == 200, response.text
    assert response.json()["message"] == "Password has been successfully reset"
    mock_reset_password.assert_called_once() 