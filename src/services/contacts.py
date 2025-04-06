from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import User
from src.repositories.contacts_repository import ContactRepository
from src.schemas.contacts import ContactSchema, ContactUpdateSchema


class ContactService:
    """
    Service layer for handling contact-related operations.

    This class provides business logic for contact management,
    interacting with the ContactRepository for database operations.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize the ContactService.

        Args:
            db: An AsyncSession object connected to the database.
        """
        self.contact_repository = ContactRepository(db)

    async def get_contacts(self, limit: int, offset: int, user: User):
        """
        Retrieve a paginated list of contacts for a specific user.

        Args:
            limit: Maximum number of contacts to return.
            offset: Number of contacts to skip before starting to return.
            user: The owner of the contacts to retrieve.

        Returns:
            A list of Contact objects.
        """
        return await self.contact_repository.get_contacts(limit, offset, user)

    async def get_contact(self, contact_id: int, user: User):
        """
        Retrieve a single contact by its ID.

        Args:
            contact_id: The ID of the contact to retrieve.
            user: The owner of the contact to retrieve.

        Returns:
            The Contact object if found, None otherwise.
        """
        return await self.contact_repository.get_contact_by_id(contact_id, user)

    async def create_contact(self, body: ContactSchema, user: User):
        """
        Create a new contact.

        Args:
            body: ContactSchema containing the contact data.
            user: The owner of the new contact.

        Returns:
            The newly created Contact object.
        """
        return await self.contact_repository.create_contact(body, user)

    async def remove_contact(self, contact_id: int, user: User):
        """
        Delete a contact by its ID.

        Args:
            contact_id: The ID of the contact to delete.
            user: The owner of the contact to delete.

        Returns:
            The deleted Contact object if found, None otherwise.
        """
        return await self.contact_repository.remove_contact(contact_id, user)

    async def update_contact(
        self, contact_id: int, body: ContactUpdateSchema, user: User
    ):
        """
        Update an existing contact.

        Args:
            contact_id: The ID of the contact to update.
            body: ContactUpdateSchema containing the updated contact data.
            user: The owner of the contact to update.

        Returns:
            The updated Contact object if found, None otherwise.
        """
        return await self.contact_repository.update_contact(contact_id, body, user)

    async def search_contacts(self, query: str, user: User):
        """
        Search contacts based on a query string.

        Args:
            query: The search string to match against contact fields.
            user: The owner of the contacts to search.

        Returns:
            A list of Contact objects matching the search criteria.
        """
        return await self.contact_repository.search_contacts(query, user)

    async def upcoming_birthdays(self, user: User):
        """
        Retrieve contacts with birthdays in the next 7 days.

        Args:
            user: The owner of the contacts to check.

        Returns:
            A list of Contact objects with birthdays in the upcoming week.
        """
        today = date.today()
        end_date = today + timedelta(days=7)
        return await self.contact_repository.get_contacts_with_birthdays(
            today, end_date, user
        )
