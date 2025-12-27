"""Base repository interface."""

from abc import ABC, abstractmethod
from typing import Generic, List, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseRepository(ABC, Generic[T]):
    """
    Abstract base repository defining common CRUD operations.

    All repository implementations must inherit from this and implement
    the abstract methods.
    """

    @abstractmethod
    async def create(self, entity: T) -> T:
        """
        Create a new entity.

        Args:
            entity: Entity to create

        Returns:
            Created entity with generated ID
        """
        pass

    @abstractmethod
    async def get_by_id(self, entity_id: UUID) -> Optional[T]:
        """
        Retrieve entity by ID.

        Args:
            entity_id: UUID of the entity

        Returns:
            Entity if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> List[T]:
        """
        Retrieve all entities with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            include_deleted: Whether to include soft-deleted records

        Returns:
            List of entities
        """
        pass

    @abstractmethod
    async def update(self, entity: T) -> T:
        """
        Update an existing entity.

        Args:
            entity: Entity with updated fields

        Returns:
            Updated entity
        """
        pass

    @abstractmethod
    async def delete(self, entity_id: UUID, soft: bool = True) -> bool:
        """
        Delete an entity.

        Args:
            entity_id: UUID of the entity to delete
            soft: If True, soft delete (set deleted_at); if False, hard delete

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def count(self, include_deleted: bool = False) -> int:
        """
        Count total entities.

        Args:
            include_deleted: Whether to include soft-deleted records

        Returns:
            Total count
        """
        pass
