import logging
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.services.contacts import ContactService
from src.schemas.contacts import ContactSchema, ContactResponse, ContactUpdateSchema
from src.conf import messages
from src.core.depend_service import get_current_user
from src.entity.models import User

router = APIRouter(prefix="/contacts", tags=["contacts"])
logger = logging.getLogger("uvicorn.error")


@router.get("/", response_model=list[ContactResponse])
async def get_contacts(
    limit: int = Query(10, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ContactResponse]:
    """
    Retrieve a paginated list of contacts for the current user.

    Args:
        limit: Maximum number of contacts to return (1-500, default: 10).
        offset: Number of contacts to skip before returning results (default: 0).
        db: Database session dependency.
        user: Authenticated user from dependency.

    Returns:
        List of ContactResponse objects.

    Notes:
        - Contacts are filtered to only those belonging to the authenticated user.
        - Default pagination returns first 10 contacts.
    """
    contact_service = ContactService(db)
    return await contact_service.get_contacts(limit, offset, user)


@router.get(
    "/{contact_id}",
    response_model=ContactResponse,
    name="Get contact by id",
    description="Retrieve a specific contact by its ID",
    response_description="The requested contact details",
)
async def get_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ContactResponse:
    """
    Retrieve a single contact by its ID.

    Args:
        contact_id: ID of the contact to retrieve.
        db: Database session dependency.
        user: Authenticated user from dependency.

    Returns:
        ContactResponse: The requested contact details.

    Raises:
        HTTPException: 404 if contact not found or doesn't belong to user.
    """
    contact_service = ContactService(db)
    contact = await contact_service.get_contact(contact_id, user)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=messages.contact_not_found.get("ua"),
        )
    return contact


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    body: ContactSchema,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ContactResponse:
    """
    Create a new contact for the current user.

    Args:
        body: Contact data to create.
        db: Database session dependency.
        user: Authenticated user from dependency.

    Returns:
        ContactResponse: The newly created contact details.

    Notes:
        - Contact is automatically associated with the authenticated user.
        - Returns HTTP 201 Created on success.
    """
    contact_service = ContactService(db)
    return await contact_service.create_contact(body, user)


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: int,
    body: ContactUpdateSchema,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ContactResponse:
    """
    Update an existing contact.

    Args:
        contact_id: ID of the contact to update.
        body: Updated contact data.
        db: Database session dependency.
        user: Authenticated user from dependency.

    Returns:
        ContactResponse: The updated contact details.

    Raises:
        HTTPException: 404 if contact not found or doesn't belong to user.
    """
    contact_service = ContactService(db)
    contact = await contact_service.update_contact(contact_id, body, user)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=messages.contact_not_found.get("ua"),
        )
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    """
    Delete a contact by its ID.

    Args:
        contact_id: ID of the contact to delete.
        db: Database session dependency.
        user: Authenticated user from dependency.

    Returns:
        None: HTTP 204 No Content on success.

    Raises:
        HTTPException: 404 if contact not found or doesn't belong to user.
    """
    contact_service = ContactService(db)
    contact = await contact_service.remove_contact(contact_id, user)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=messages.contact_not_found.get("ua"),
        )
    return None


@router.get(
    "/search/",
    response_model=list[ContactResponse],
    description="Search contacts by name, last name, or email address",
)
async def search_contacts(
    query: str = Query(..., description=messages.contact_search_description.get("ua")),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ContactResponse]:
    """
    Search contacts matching the query string.

    Args:
        query: Search string to match against name, last name, or email.
        db: Database session dependency.
        user: Authenticated user from dependency.

    Returns:
        List of matching ContactResponse objects.

    Notes:
        - Search is case-insensitive.
        - Only returns contacts belonging to the authenticated user.
    """
    contact_service = ContactService(db)
    return await contact_service.search_contacts(query, user)


@router.get(
    "/upcoming_birthdays/",
    response_model=list[ContactResponse],
    description="Get contacts with birthdays in the next 7 days",
)
async def get_upcoming_birthdays(
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
) -> list[ContactResponse]:
    """
    Retrieve contacts with upcoming birthdays (next 7 days).

    Args:
        db: Database session dependency.
        user: Authenticated user from dependency.

    Returns:
        List of ContactResponse objects with upcoming birthdays.

    Notes:
        - Includes birthdays from today to 7 days in the future.
        - Only returns contacts belonging to the authenticated user.
    """
    contact_service = ContactService(db)
    return await contact_service.upcoming_birthdays(user)
