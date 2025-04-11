import pytest
from sqlalchemy import select
from unittest.mock import Mock, patch

from src.entity.models import User
from tests.conftest import TestingSessionLocal

new_user_data = {
    "username": "spiderman",
    "email": "spiderman@example.com",
    "password": "webslinger12",
}


def test_register(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.services.email.send_email", mock_send_email)

    response = client.post("api/auth/register", json=new_user_data)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["username"] == new_user_data["username"]
    assert data["email"] == new_user_data["email"]
    assert "hash_password" not in data
    assert "avatar" in data


def test_register_existing_username(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.services.email.send_email", mock_send_email)

    duplicate_user = new_user_data.copy()
    duplicate_user["email"] = "another_email@example.com"
    response = client.post("api/auth/register", json=duplicate_user)
    assert response.status_code == 409, response.text
    assert response.json()["detail"] == "Користувач вже існує"


def test_register_existing_email(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.services.email.send_email", mock_send_email)

    duplicate_user = new_user_data.copy()
    duplicate_user["username"] = "batman"
    response = client.post("api/auth/register", json=duplicate_user)
    assert response.status_code == 409, response.text
    assert response.json()["detail"] == "Email вже існує"


def test_login_unconfirmed_user(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.services.email.send_email", mock_send_email)

    unconfirmed_data = {
        "username": "ghostuser",
        "email": "ghost@web.com",
        "password": "ghost123",
    }
    client.post("api/auth/register", json=unconfirmed_data)

    response = client.post(
        "api/auth/login",
        data={
            "username": unconfirmed_data["username"],
            "password": unconfirmed_data["password"],
        },
    )
    assert response.status_code == 401, response.text
    assert response.json()["detail"] == "Email не підтверджено"


@pytest.mark.asyncio
async def test_login_confirmed_user(client):
    async with TestingSessionLocal() as session:
        user = await session.execute(
            select(User).where(User.email == new_user_data["email"])
        )
        user = user.scalar_one_or_none()
        user.confirmed = True
        await session.commit()

    response = client.post(
        "api/auth/login",
        data={
            "username": new_user_data["username"],
            "password": new_user_data["password"],
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    response = client.post(
        "api/auth/login",
        data={"username": new_user_data["username"], "password": "wrongpassword"},
    )
    assert response.status_code == 401, response.text
    assert response.json()["detail"] == "Неправильне ім'я користувача або пароль"


def test_login_wrong_username(client):
    response = client.post(
        "api/auth/login",
        data={"username": "nonexistentuser", "password": new_user_data["password"]},
    )
    assert response.status_code == 401, response.text
    assert response.json()["detail"] == "Неправильне ім'я користувача або пароль"


def test_login_validation_error(client):
    response = client.post(
        "api/auth/login", data={"password": new_user_data["password"]}
    )
    assert response.status_code == 422, response.text
    assert "detail" in response.json()


def test_token_refresh(client):
    login = client.post(
        "api/auth/login",
        data={
            "username": new_user_data["username"],
            "password": new_user_data["password"],
        },
    )
    assert login.status_code == 200
    old_refresh_token = login.json()["refresh_token"]

    refresh = client.post("api/auth/refresh", json={"refresh_token": old_refresh_token})
    assert refresh.status_code == 200, refresh.text
    data = refresh.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["refresh_token"] != old_refresh_token


def test_logout_user(client):
    login = client.post(
        "api/auth/login",
        data={
            "username": new_user_data["username"],
            "password": new_user_data["password"],
        },
    )

    assert login.status_code == 200
    data = login.json()
    access_token = data["access_token"]
    refresh_token = data["refresh_token"]

    logout = client.post(
        "api/auth/logout",
        json={"refresh_token": refresh_token},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert logout.status_code == 204
