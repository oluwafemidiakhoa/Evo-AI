"""PostgreSQL implementation of Round repository."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from evo_ai.domain.models.round import Round, RoundStatus
from evo_ai.domain.repositories.round_repo import RoundRepository
from evo_ai.infrastructure.database.models import RoundDB, RoundStatusEnum


class PostgresRoundRepository(RoundRepository):
    """PostgreSQL implementation of RoundRepository."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def create(self, entity: Round) -> Round:
        """Create a new round."""
        db_round = RoundDB(
            id=entity.id,
            campaign_id=entity.campaign_id,
            round_number=entity.round_number,
            status=RoundStatusEnum(entity.status.value),
            plan=entity.plan,
            meta_data={},
            metrics=entity.metrics,
            started_at=entity.started_at,
            completed_at=entity.completed_at,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
        self.session.add(db_round)
        await self.session.flush()
        return self._to_domain(db_round)

    async def get_by_id(self, entity_id: UUID) -> Optional[Round]:
        """Retrieve round by ID."""
        result = await self.session.execute(
            select(RoundDB).where(
                RoundDB.id == entity_id,
                RoundDB.deleted_at.is_(None)
            )
        )
        db_round = result.scalar_one_or_none()
        return self._to_domain(db_round) if db_round else None

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> List[Round]:
        """Retrieve all rounds with pagination."""
        query = select(RoundDB)

        if not include_deleted:
            query = query.where(RoundDB.deleted_at.is_(None))

        query = query.offset(skip).limit(limit).order_by(desc(RoundDB.created_at))

        result = await self.session.execute(query)
        db_rounds = result.scalars().all()
        return [self._to_domain(db_r) for db_r in db_rounds]

    async def update(self, entity: Round) -> Round:
        """Update an existing round."""
        result = await self.session.execute(
            select(RoundDB).where(RoundDB.id == entity.id)
        )
        db_round = result.scalar_one_or_none()

        if not db_round:
            raise ValueError(f"Round {entity.id} not found")

        # Update fields
        db_round.status = RoundStatusEnum(entity.status.value)
        db_round.plan = entity.plan
        db_round.metrics = entity.metrics
        db_round.started_at = entity.started_at
        db_round.completed_at = entity.completed_at
        db_round.updated_at = datetime.utcnow()

        await self.session.flush()
        return self._to_domain(db_round)

    async def delete(self, entity_id: UUID, soft: bool = True) -> bool:
        """Delete a round."""
        result = await self.session.execute(
            select(RoundDB).where(RoundDB.id == entity_id)
        )
        db_round = result.scalar_one_or_none()

        if not db_round:
            return False

        if soft:
            db_round.deleted_at = datetime.utcnow()
            await self.session.flush()
        else:
            await self.session.delete(db_round)

        return True

    async def count(self, include_deleted: bool = False) -> int:
        """Count total rounds."""
        query = select(func.count(RoundDB.id))

        if not include_deleted:
            query = query.where(RoundDB.deleted_at.is_(None))

        result = await self.session.execute(query)
        return result.scalar_one()

    async def get_by_campaign(
        self,
        campaign_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Round]:
        """Retrieve all rounds for a campaign."""
        result = await self.session.execute(
            select(RoundDB).where(
                RoundDB.campaign_id == campaign_id,
                RoundDB.deleted_at.is_(None)
            ).order_by(RoundDB.round_number.asc())
            .offset(skip).limit(limit)
        )
        db_rounds = result.scalars().all()
        return [self._to_domain(db_r) for db_r in db_rounds]

    async def get_by_campaign_id(self, campaign_id: UUID) -> List[Round]:
        """Backwards-compatible alias for get_by_campaign."""
        return await self.get_by_campaign(campaign_id)

    async def get_latest_round(self, campaign_id: UUID) -> Optional[Round]:
        """Get the most recent round for a campaign."""
        result = await self.session.execute(
            select(RoundDB).where(
                RoundDB.campaign_id == campaign_id,
                RoundDB.deleted_at.is_(None)
            ).order_by(desc(RoundDB.round_number))
            .limit(1)
        )
        db_round = result.scalar_one_or_none()
        return self._to_domain(db_round) if db_round else None

    async def get_by_status(
        self,
        status: RoundStatus,
        campaign_id: Optional[UUID] = None
    ) -> List[Round]:
        """Retrieve rounds by status, optionally filtered by campaign."""
        query = select(RoundDB).where(
            RoundDB.status == RoundStatusEnum(status.value),
            RoundDB.deleted_at.is_(None)
        )

        if campaign_id:
            query = query.where(RoundDB.campaign_id == campaign_id)

        query = query.order_by(desc(RoundDB.created_at))

        result = await self.session.execute(query)
        db_rounds = result.scalars().all()
        return [self._to_domain(db_r) for db_r in db_rounds]

    async def get_next_round_number(self, campaign_id: UUID) -> int:
        """Get the next round number for a campaign."""
        result = await self.session.execute(
            select(func.max(RoundDB.round_number)).where(
                RoundDB.campaign_id == campaign_id
            )
        )
        max_round = result.scalar_one_or_none()
        return (max_round or 0) + 1

    @staticmethod
    def _to_domain(db_round: RoundDB) -> Round:
        """Convert database model to domain model."""
        return Round(
            id=db_round.id,
            campaign_id=db_round.campaign_id,
            round_number=db_round.round_number,
            status=RoundStatus(db_round.status.value),
            plan=db_round.plan,
            metrics=db_round.metrics,
            started_at=db_round.started_at,
            completed_at=db_round.completed_at,
            created_at=db_round.created_at,
            updated_at=db_round.updated_at,
            deleted_at=db_round.deleted_at,
        )
