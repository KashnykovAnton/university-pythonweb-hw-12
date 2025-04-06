import pytest
from unittest.mock import AsyncMock, Mock
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from src.entity.models import Contact, User
from src.repositories.contacts_repository import ContactRepository
from src.schemas.contacts import ContactSchema, ContactUpdateSchema


@pytest.fixture
def mock_session():
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = Mock()
    session.delete = AsyncMock()
    return session


@pytest.fixture
def contact_repository(mock_session):
    return ContactRepository(mock_session)


@pytest.fixture
def mock_user():
    return User(id=1)


@pytest.mark.asyncio
async def test_get_contacts(contact_repository, mock_session, mock_user):
    # Arrange
    mock_contact = Contact(id=1, user_id=mock_user.id)
    mock_result = Mock()
    mock_result.scalars.return_value.all.return_value = [mock_contact]
    mock_session.execute.return_value = mock_result

    # Act
    result = await contact_repository.get_contacts(limit=10, offset=0, user=mock_user)

    # Assert
    assert result == [mock_contact]
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_contact_by_id(contact_repository, mock_session, mock_user):
    # Arrange
    mock_contact = Contact(id=1, user_id=mock_user.id)
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = mock_contact
    mock_session.execute.return_value = mock_result

    # Act
    result = await contact_repository.get_contact_by_id(contact_id=1, user=mock_user)

    # Assert
    assert result == mock_contact
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_create_contact(contact_repository, mock_session, mock_user):
    # Arrange
    contact_data = ContactSchema(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        phone_number="1234567890",
        birthday=date(1990, 1, 1),
        address="123 Street",
    )
    expected_contact = Contact(**contact_data.model_dump(), user=mock_user)
    mock_session.refresh.return_value = expected_contact

    # Act
    result = await contact_repository.create_contact(contact_data, mock_user)

    # Assert
    assert result.first_name == contact_data.first_name
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()


@pytest.mark.asyncio
async def test_remove_contact(contact_repository, mock_session, mock_user):
    # Arrange
    mock_contact = Contact(id=1, user_id=mock_user.id)
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = mock_contact
    mock_session.execute.return_value = mock_result

    # Act
    result = await contact_repository.remove_contact(contact_id=1, user=mock_user)

    # Assert
    assert result == mock_contact
    mock_session.delete.assert_called_once_with(mock_contact)
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_contact(contact_repository, mock_session, mock_user):
    # Arrange
    mock_contact = Contact(id=1, user_id=mock_user.id, phone_number="123456789")
    updated_data = ContactUpdateSchema(phone_number="987654321")
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = mock_contact
    mock_session.execute.return_value = mock_result
    mock_session.refresh.return_value = mock_contact

    # Act
    result = await contact_repository.update_contact(
        contact_id=1, body=updated_data, user=mock_user
    )

    # Assert
    assert result.phone_number == "987654321"
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()


@pytest.mark.asyncio
async def test_search_contacts(contact_repository, mock_session, mock_user):
    # Arrange
    mock_contact = Contact(id=1, user_id=mock_user.id)
    mock_result = Mock()
    mock_result.scalars.return_value.all.return_value = [mock_contact]
    mock_session.execute.return_value = mock_result

    # Act
    result = await contact_repository.search_contacts(query="john", user=mock_user)

    # Assert
    assert result == [mock_contact]
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_contacts_with_birthdays(contact_repository, mock_session, mock_user):
    # Arrange
    mock_contact = Contact(id=1, user_id=mock_user.id, birthday=date(1990, 4, 5))
    mock_result = Mock()
    mock_result.scalars.return_value.all.return_value = [mock_contact]
    mock_session.execute.return_value = mock_result

    # Act
    result = await contact_repository.get_contacts_with_birthdays(
        start_date=date(2023, 4, 1), end_date=date(2023, 4, 30), user=mock_user
    )

    # Assert
    assert result == [mock_contact]
    mock_session.execute.assert_called_once()
