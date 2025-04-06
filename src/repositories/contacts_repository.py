import logging
from typing import Sequence

from sqlalchemy import select, or_, func, asc
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import User
from src.entity.models import Contact
from src.schemas.contacts import ContactSchema, ContactUpdateSchema
from datetime import date

logger = logging.getLogger("uvicorn.error")


class ContactRepository:
    def __init__(self, session: AsyncSession):
        """
        Initialize a ContactRepository.

        Args:
            session: An asynchronous SQLAlchemy session.
        """
        self.db = session

    async def get_contacts(
        self, limit: int, offset: int, user: User
    ) -> Sequence[Contact]:
        """
        Retrieve a paginated list of contacts for a user.

        Args:
            limit: Maximum number of contacts to return.
            offset: Number of contacts to skip.
            user: The user whose contacts are retrieved.

        Returns:
            A list of Contact instances.
        """
        stmt = (
            select(Contact)
            .filter_by(user_id=user.id)
            .order_by(Contact.id)
            .offset(offset)
            .limit(limit)
        )
        contacts = await self.db.execute(stmt)
        return contacts.scalars().all()

    async def get_contact_by_id(self, contact_id: int, user: User) -> Contact | None:
        """
        Retrieve a contact by its ID and user.

        Args:
            contact_id: The ID of the contact.
            user: The user who owns the contact.

        Returns:
            A Contact instance if found, otherwise None.
        """
        stmt = select(Contact).filter_by(id=contact_id, user_id=user.id)
        contact = await self.db.execute(stmt)
        return contact.scalar_one_or_none()

    async def create_contact(self, body: ContactSchema, user: User) -> Contact:
        """
        Create a new contact for the user.

        Args:
            body: Schema containing contact creation data.
            user: The user creating the contact.

        Returns:
            The created Contact instance.
        """
        contact = Contact(**body.model_dump(), user=user)
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def remove_contact(self, contact_id: int, user: User) -> Contact | None:
        """
        Delete a contact by its ID and user.

        Args:
            contact_id: The ID of the contact to delete.
            user: The user who owns the contact.

        Returns:
            The deleted Contact instance if found, otherwise None.
        """
        contact = await self.get_contact_by_id(contact_id, user)
        if contact:
            await self.db.delete(contact)
            await self.db.commit()
        return contact

    async def update_contact(
        self, contact_id: int, body: ContactUpdateSchema, user: User
    ) -> Contact | None:
        """
        Update a contact with new data.

        Args:
            contact_id: The ID of the contact to update.
            body: Schema containing fields to update.
            user: The user who owns the contact.

        Returns:
            The updated Contact instance if found, otherwise None.
        """
        contact = await self.get_contact_by_id(contact_id, user)
        if contact:
            update_data = body.model_dump(exclude_unset=True)

            for key, value in update_data.items():
                setattr(contact, key, value)

            await self.db.commit()
            await self.db.refresh(contact)

        return contact

    async def search_contacts(self, query: str, user: User) -> Sequence[Contact]:
        """
        Search user's contacts by name or email.

        Args:
            query: Search string.
            user: The user performing the search.

        Returns:
            A list of matching Contact instances.
        """
        stmt = (
            select(Contact)
            .filter_by(user_id=user.id)
            .where(
                or_(
                    Contact.first_name.ilike(f"%{query}%"),
                    Contact.last_name.ilike(f"%{query}%"),
                    Contact.email.ilike(f"%{query}%"),
                )
            )
            .order_by(Contact.id)
        )
        contacts = await self.db.execute(stmt)
        return contacts.scalars().all()

    async def get_contacts_with_birthdays(
        self, start_date: date, end_date: date, user: User
    ) -> Sequence[Contact]:
        """
        Retrieve contacts with birthdays between two dates (month/day only).

        Args:
            start_date: Start date of the range.
            end_date: End date of the range.
            user: The user whose contacts to check.

        Returns:
            A list of Contact instances with birthdays in the given range.
        """
        stmt = (
            select(Contact)
            .filter_by(user_id=user.id)
            .where(
                func.to_char(Contact.birthday, "MM-DD").between(
                    func.to_char(start_date, "MM-DD"), func.to_char(end_date, "MM-DD")
                )
            )
            .order_by(asc(func.to_char(Contact.birthday, "MM-DD")))
        )
        contacts = await self.db.execute(stmt)
        return contacts.scalars().all()
