"""PostgreSQL implementation of Variant repository."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from evo_ai.domain.models.variant import Variant
from evo_ai.domain.repositories.variant_repo import VariantRepository
from evo_ai.infrastructure.database.models import RoundDB, VariantDB


class PostgresVariantRepository(VariantRepository):
    """PostgreSQL implementation of VariantRepository."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def create(self, entity: Variant) -> Variant:
        """Create a new variant."""
        db_variant = VariantDB(
            id=entity.id,
            round_id=entity.round_id,
            parent_id=entity.parent_id,
            generation=entity.generation,
            content=entity.content,
            content_hash=entity.content_hash,
            mutation_type=entity.mutation_type,
            mutation_metadata=entity.mutation_metadata,
            is_selected=entity.is_selected,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
        self.session.add(db_variant)
        await self.session.flush()
        return self._to_domain(db_variant)

    async def get_by_id(self, entity_id: UUID) -> Optional[Variant]:
        """Retrieve variant by ID."""
        result = await self.session.execute(
            select(VariantDB).where(
                VariantDB.id == entity_id,
                VariantDB.deleted_at.is_(None)
            )
        )
        db_variant = result.scalar_one_or_none()
        return self._to_domain(db_variant) if db_variant else None

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> List[Variant]:
        """Retrieve all variants with pagination."""
        query = select(VariantDB)

        if not include_deleted:
            query = query.where(VariantDB.deleted_at.is_(None))

        query = query.offset(skip).limit(limit).order_by(desc(VariantDB.created_at))

        result = await self.session.execute(query)
        db_variants = result.scalars().all()
        return [self._to_domain(db_v) for db_v in db_variants]

    async def update(self, entity: Variant) -> Variant:
        """Update an existing variant."""
        result = await self.session.execute(
            select(VariantDB).where(VariantDB.id == entity.id)
        )
        db_variant = result.scalar_one_or_none()

        if not db_variant:
            raise ValueError(f"Variant {entity.id} not found")

        # Update fields
        db_variant.is_selected = entity.is_selected
        db_variant.mutation_metadata = entity.mutation_metadata
        db_variant.updated_at = datetime.utcnow()

        await self.session.flush()
        return self._to_domain(db_variant)

    async def delete(self, entity_id: UUID, soft: bool = True) -> bool:
        """Delete a variant."""
        result = await self.session.execute(
            select(VariantDB).where(VariantDB.id == entity_id)
        )
        db_variant = result.scalar_one_or_none()

        if not db_variant:
            return False

        if soft:
            db_variant.deleted_at = datetime.utcnow()
            await self.session.flush()
        else:
            await self.session.delete(db_variant)

        return True

    async def count(self, include_deleted: bool = False) -> int:
        """Count total variants."""
        query = select(func.count(VariantDB.id))

        if not include_deleted:
            query = query.where(VariantDB.deleted_at.is_(None))

        result = await self.session.execute(query)
        return result.scalar_one()

    async def get_by_round(
        self,
        round_id: UUID,
        skip: int = 0,
        limit: int = 1000
    ) -> List[Variant]:
        """Retrieve all variants for a round."""
        result = await self.session.execute(
            select(VariantDB).where(
                VariantDB.round_id == round_id,
                VariantDB.deleted_at.is_(None)
            ).order_by(VariantDB.created_at.asc())
            .offset(skip).limit(limit)
        )
        db_variants = result.scalars().all()
        return [self._to_domain(db_v) for db_v in db_variants]

    async def get_selected_variants(self, round_id: UUID) -> List[Variant]:
        """Retrieve variants marked as selected for next round."""
        result = await self.session.execute(
            select(VariantDB).where(
                VariantDB.round_id == round_id,
                VariantDB.is_selected == True,  # noqa: E712
                VariantDB.deleted_at.is_(None)
            ).order_by(VariantDB.created_at.asc())
        )
        db_variants = result.scalars().all()
        return [self._to_domain(db_v) for db_v in db_variants]

    async def get_by_parent(self, parent_id: UUID) -> List[Variant]:
        """Retrieve all child variants of a parent."""
        result = await self.session.execute(
            select(VariantDB).where(
                VariantDB.parent_id == parent_id,
                VariantDB.deleted_at.is_(None)
            ).order_by(VariantDB.created_at.asc())
        )
        db_variants = result.scalars().all()
        return [self._to_domain(db_v) for db_v in db_variants]

    async def get_lineage(self, variant_id: UUID) -> List[Variant]:
        """
        Retrieve the full lineage (ancestry) of a variant.

        This recursively follows parent_id links back to generation 0.
        Uses recursive CTE for efficient querying.
        """
        # Recursive CTE to trace lineage
        cte = select(VariantDB).where(VariantDB.id == variant_id).cte(recursive=True)

        cte_alias = cte.alias()
        variant_alias = VariantDB.__table__.alias()

        cte = cte.union_all(
            select(variant_alias).where(
                variant_alias.c.id == cte_alias.c.parent_id
            )
        )

        result = await self.session.execute(
            select(VariantDB).from_statement(
                select(cte).order_by(cte.c.generation.asc())
            )
        )
        db_variants = result.scalars().all()
        return [self._to_domain(db_v) for db_v in db_variants]

    async def get_by_content_hash(self, content_hash: str) -> Optional[Variant]:
        """Find variant by content hash (for deduplication)."""
        result = await self.session.execute(
            select(VariantDB).where(
                VariantDB.content_hash == content_hash,
                VariantDB.deleted_at.is_(None)
            )
        )
        db_variant = result.scalar_one_or_none()
        return self._to_domain(db_variant) if db_variant else None

    async def get_by_generation(
        self,
        campaign_id: UUID,
        generation: int
    ) -> List[Variant]:
        """Retrieve all variants at a specific generation across all rounds."""
        # Join with rounds to filter by campaign
        result = await self.session.execute(
            select(VariantDB)
            .join(RoundDB, VariantDB.round_id == RoundDB.id)
            .where(
                RoundDB.campaign_id == campaign_id,
                VariantDB.generation == generation,
                VariantDB.deleted_at.is_(None),
                RoundDB.deleted_at.is_(None)
            ).order_by(VariantDB.created_at.asc())
        )
        db_variants = result.scalars().all()
        return [self._to_domain(db_v) for db_v in db_variants]

    @staticmethod
    def _to_domain(db_variant: VariantDB) -> Variant:
        """Convert database model to domain model."""
        return Variant(
            id=db_variant.id,
            round_id=db_variant.round_id,
            parent_id=db_variant.parent_id,
            generation=db_variant.generation,
            content=db_variant.content,
            mutation_type=db_variant.mutation_type,
            mutation_metadata=db_variant.mutation_metadata,
            is_selected=db_variant.is_selected,
            created_at=db_variant.created_at,
            updated_at=db_variant.updated_at,
            deleted_at=db_variant.deleted_at,
        )
