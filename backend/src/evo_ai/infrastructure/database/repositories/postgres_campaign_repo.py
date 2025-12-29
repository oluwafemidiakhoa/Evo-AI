"""PostgreSQL implementation of Campaign repository."""

import json
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import insert, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from evo_ai.domain.models.campaign import Campaign, CampaignStatus
from evo_ai.domain.repositories.campaign_repo import CampaignRepository
from evo_ai.infrastructure.database.models import CampaignDB, CampaignStatusEnum


class PostgresCampaignRepository(CampaignRepository):
    """PostgreSQL implementation of CampaignRepository."""

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def create(self, entity: Campaign) -> Campaign:
        """Create a new campaign."""
        # Use raw SQL to completely bypass SQLModel/Pydantic v2 default_factory issues
        stmt = text("""
            INSERT INTO campaigns (id, name, description, status, config, meta_data, created_at, updated_at)
            VALUES (:id, :name, :description, :status, :config, :meta_data, :created_at, :updated_at)
        """)

        await self.session.execute(stmt, {
            "id": str(entity.id),
            "name": entity.name,
            "description": entity.description,
            "status": entity.status.name.upper(),  # Use enum name instead of value
            "config": json.dumps(entity.config),
            "meta_data": json.dumps(entity.metadata),
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
        })
        await self.session.flush()

        # Fetch the created campaign using ORM select (not instantiation)
        return await self.get_by_id(entity.id)

    async def get_by_id(self, entity_id: UUID) -> Optional[Campaign]:
        """Retrieve campaign by ID."""
        result = await self.session.execute(
            select(CampaignDB).where(
                CampaignDB.id == entity_id,
                CampaignDB.deleted_at.is_(None)
            )
        )
        db_campaign = result.scalar_one_or_none()
        return self._to_domain(db_campaign) if db_campaign else None

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> List[Campaign]:
        """Retrieve all campaigns with pagination."""
        query = select(CampaignDB)

        if not include_deleted:
            query = query.where(CampaignDB.deleted_at.is_(None))

        query = query.offset(skip).limit(limit).order_by(CampaignDB.created_at.desc())

        result = await self.session.execute(query)
        db_campaigns = result.scalars().all()
        return [self._to_domain(db_c) for db_c in db_campaigns]

    async def update(self, entity: Campaign) -> Campaign:
        """Update an existing campaign."""
        result = await self.session.execute(
            select(CampaignDB).where(CampaignDB.id == entity.id)
        )
        db_campaign = result.scalar_one_or_none()

        if not db_campaign:
            raise ValueError(f"Campaign {entity.id} not found")

        # Update fields
        db_campaign.name = entity.name
        db_campaign.description = entity.description
        db_campaign.status = CampaignStatusEnum(entity.status.value)
        db_campaign.config = entity.config
        db_campaign.meta_data = entity.metadata
        db_campaign.updated_at = datetime.utcnow()

        await self.session.flush()
        return self._to_domain(db_campaign)

    async def delete(self, entity_id: UUID, soft: bool = True) -> bool:
        """Delete a campaign."""
        result = await self.session.execute(
            select(CampaignDB).where(CampaignDB.id == entity_id)
        )
        db_campaign = result.scalar_one_or_none()

        if not db_campaign:
            return False

        if soft:
            db_campaign.deleted_at = datetime.utcnow()
            await self.session.flush()
        else:
            await self.session.delete(db_campaign)

        return True

    async def count(self, include_deleted: bool = False) -> int:
        """Count total campaigns."""
        query = select(CampaignDB)

        if not include_deleted:
            query = query.where(CampaignDB.deleted_at.is_(None))

        result = await self.session.execute(query)
        return len(result.scalars().all())

    async def get_by_status(
        self,
        status: CampaignStatus,
        skip: int = 0,
        limit: int = 100
    ) -> List[Campaign]:
        """Retrieve campaigns by status."""
        result = await self.session.execute(
            select(CampaignDB).where(
                CampaignDB.status == CampaignStatusEnum(status.value),
                CampaignDB.deleted_at.is_(None)
            ).offset(skip).limit(limit).order_by(CampaignDB.created_at.desc())
        )
        db_campaigns = result.scalars().all()
        return [self._to_domain(db_c) for db_c in db_campaigns]

    async def get_active_campaigns(self) -> List[Campaign]:
        """Retrieve all active campaigns."""
        result = await self.session.execute(
            select(CampaignDB).where(
                CampaignDB.status == CampaignStatusEnum.ACTIVE,
                CampaignDB.deleted_at.is_(None)
            ).order_by(CampaignDB.created_at.desc())
        )
        db_campaigns = result.scalars().all()
        return [self._to_domain(db_c) for db_c in db_campaigns]

    async def get_by_name(self, name: str) -> Optional[Campaign]:
        """Retrieve campaign by name."""
        result = await self.session.execute(
            select(CampaignDB).where(
                CampaignDB.name == name,
                CampaignDB.deleted_at.is_(None)
            )
        )
        db_campaign = result.scalar_one_or_none()
        return self._to_domain(db_campaign) if db_campaign else None

    @staticmethod
    def _to_domain(db_campaign: CampaignDB) -> Campaign:
        """Convert database model to domain model."""
        return Campaign(
            id=db_campaign.id,
            name=db_campaign.name,
            description=db_campaign.description,
            status=CampaignStatus(db_campaign.status.value),
            config=db_campaign.config,
            metadata=db_campaign.meta_data,
            created_at=db_campaign.created_at,
            updated_at=db_campaign.updated_at,
            deleted_at=db_campaign.deleted_at,
        )
