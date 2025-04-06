from typing import TypeVar, Type

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository:
    def __init__(self, session: AsyncSession, model: Type[ModelType]):
        """
        Initialize a BaseRepository.

        Args:
            session: An AsyncSession instance for DB interaction.
            model: A SQLAlchemy model class.
        """
        self.db = session
        self.model = model

    async def get_all(self) -> list[ModelType]:
        """
        Retrieve all records of the model.

        Returns:
            A list of model instances.
        """
        stmt = select(self.model)
        contacts = await self.db.execute(stmt)
        return list(contacts.scalars().all())

    async def get_by_id(self, _id: int) -> ModelType | None:
        """
        Retrieve a model instance by its ID.

        Args:
            _id: The ID of the model instance.

        Returns:
            A model instance if found, otherwise None.
        """
        result = await self.db.execute(select(self.model).where(self.model.id == _id))
        return result.scalars().first()

    async def create(self, instance: ModelType) -> ModelType:
        """
        Add a new model instance to the database.

        Args:
            instance: The instance to be added.

        Returns:
            The created and refreshed instance.
        """
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def update(self, instance: ModelType) -> ModelType:
        """
        Update an existing model instance.

        Args:
            instance: The instance to be updated.

        Returns:
            The updated and refreshed instance.
        """
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def delete(self, instance: ModelType) -> None:
        """
        Delete a model instance from the database.

        Args:
            instance: The instance to be deleted.
        """
        await self.db.delete(instance)
        await self.db.commit()
