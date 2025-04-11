from datetime import date, timedelta
import pytest

test_contact_data = {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "phone_number": "1234567890",
    "birthday": "1990-01-01",
    "additional_info": "123 Main St"
}


def test_create_contact(client, get_token):
    response = client.post(
        "/api/contacts",
        json=test_contact_data,
        headers={"Authorization": f"Bearer {get_token}"},
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["first_name"] == test_contact_data["first_name"]
    assert data["last_name"] == test_contact_data["last_name"]
    assert data["email"] == test_contact_data["email"]
    assert data["phone_number"] == test_contact_data["phone_number"]
    assert data["birthday"] == test_contact_data["birthday"]
    assert data["additional_info"] == test_contact_data["additional_info"]
    assert "id" in data


def test_get_contact(client, get_token):
    response = client.get(
        "/api/contacts/1",
        headers={"Authorization": f"Bearer {get_token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["first_name"] == test_contact_data["first_name"]
    assert data["last_name"] == test_contact_data["last_name"]
    assert data["email"] == test_contact_data["email"]
    assert "id" in data


def test_get_contact_not_found(client, get_token):
    response = client.get(
        "/api/contacts/999",
        headers={"Authorization": f"Bearer {get_token}"},
    )
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == "Контакт не знайдено"


def test_get_contacts(client, get_token):
    response = client.get(
        "/api/contacts",
        headers={"Authorization": f"Bearer {get_token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["first_name"] == test_contact_data["first_name"]
    assert "id" in data[0]


def test_update_contact(client, get_token):
    updated_data = {
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "jane@example.com",
        "phone_number": "0987654321",
        "birthday": "1995-05-05",
        "additional_info": "456 Oak St"
    }
    response = client.put(
        "/api/contacts/1",
        json=updated_data,
        headers={"Authorization": f"Bearer {get_token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["first_name"] == updated_data["first_name"]
    assert data["last_name"] == updated_data["last_name"]
    assert data["email"] == updated_data["email"]
    assert data["phone_number"] == updated_data["phone_number"]
    assert data["birthday"] == updated_data["birthday"]
    assert data["additional_info"] == updated_data["additional_info"]
    assert "id" in data


def test_update_contact_not_found(client, get_token):
    response = client.put(
        "/api/contacts/999",
        json={"first_name": "Jane"},
        headers={"Authorization": f"Bearer {get_token}"},
    )
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == "Контакт не знайдено"


def test_delete_contact(client, get_token):
    response = client.delete(
        "/api/contacts/1",
        headers={"Authorization": f"Bearer {get_token}"},
    )
    assert response.status_code == 204, response.text


def test_delete_contact_not_found(client, get_token):
    response = client.delete(
        "/api/contacts/999",
        headers={"Authorization": f"Bearer {get_token}"},
    )
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == "Контакт не знайдено"


def test_search_contacts(client, get_token):
    # Create a new contact for searching
    client.post(
        "/api/contacts",
        json=test_contact_data,
        headers={"Authorization": f"Bearer {get_token}"},
    )

    response = client.get(
        "/api/contacts/search/?query=John",
        headers={"Authorization": f"Bearer {get_token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["first_name"] == test_contact_data["first_name"]


@pytest.mark.skip(reason="Requires PostgreSQL for to_char function")
def test_get_upcoming_birthdays(client, get_token):
    # Create a contact with upcoming birthday
    tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    upcoming_birthday_contact = {
        "first_name": "Birthday",
        "last_name": "Person",
        "email": "birthday@example.com",
        "phone_number": "1111111111",
        "birthday": tomorrow,
        "additional_info": "Birthday St"
    }
    client.post(
        "/api/contacts",
        json=upcoming_birthday_contact,
        headers={"Authorization": f"Bearer {get_token}"},
    )

    response = client.get(
        "/api/contacts/upcoming_birthdays/",
        headers={"Authorization": f"Bearer {get_token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data) == 1
    assert data[0]["first_name"] == "Birthday"
    assert data[0]["last_name"] == "Person"
    assert data[0]["email"] == "birthday@example.com"
    assert data[0]["birthday"] == tomorrow 