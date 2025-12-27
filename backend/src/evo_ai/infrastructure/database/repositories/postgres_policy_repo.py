"""PostgreSQL implementation of Policy repository."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from evo_ai.domain.models.policy import Policy, PolicyType
from evo_ai.domain.repositories.policy_repo import PolicyRepository
from evo_ai.infrastructure.database.models import PolicyDB, PolicyTypeEnum


class PostgresPolicyRepository(PolicyRepository):
    """PostgreSQL implementation of PolicyRepository."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def create(self, entity: Policy) -> Policy:
        """Create a new policy."""
        db_policy = PolicyDB(
            id=entity.id,
            campaign_id=entity.campaign_id,
            name=entity.name,
            policy_type=PolicyTypeEnum(entity.policy_type.value),
            version=entity.version,
            config=entity.config,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
        self.session.add(db_policy)
        await self.session.flush()
        return self._to_domain(db_policy)

    async def get_by_id(self, entity_id: UUID) -> Optional[Policy]:
        """Retrieve policy by ID."""
        result = await self.session.execute(
            select(PolicyDB).where(
                PolicyDB.id == entity_id,
                PolicyDB.deleted_at.is_(None)
            )
        )
        db_policy = result.scalar_one_or_none()
        return self._to_domain(db_policy) if db_policy else None

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> List[Policy]:
        """Retrieve all policies with pagination."""
        query = select(PolicyDB)

        if not include_deleted:
            query = query.where(PolicyDB.deleted_at.is_(None))

        query = query.offset(skip).limit(limit).order_by(desc(PolicyDB.created_at))

        result = await self.session.execute(query)
        db_policies = result.scalars().all()
        return [self._to_domain(db_p) for db_p in db_policies]

    async def update(self, entity: Policy) -> Policy:
        """Update an existing policy."""
        result = await self.session.execute(
            select(PolicyDB).where(PolicyDB.id == entity.id)
        )
        db_policy = result.scalar_one_or_none()

        if not db_policy:
            raise ValueError(f"Policy {entity.id} not found")

        # Update fields
        db_policy.name = entity.name
        db_policy.config = entity.config
        db_policy.is_active = entity.is_active
        db_policy.updated_at = datetime.utcnow()

        await self.session.flush()
        return self._to_domain(db_policy)

    async def delete(self, entity_id: UUID, soft: bool = True) -> bool:
        """Delete a policy."""
        result = await self.session.execute(
            select(PolicyDB).where(PolicyDB.id == entity_id)
        )
        db_policy = result.scalar_one_or_none()

        if not db_policy:
            return False

        if soft:
            db_policy.deleted_at = datetime.utcnow()
            await self.session.flush()
        else:
            await self.session.delete(db_policy)

        return True

    async def count(self, include_deleted: bool = False) -> int:
        """Count total policies."""
        query = select(func.count(PolicyDB.id))

        if not include_deleted:
            query = query.where(PolicyDB.deleted_at.is_(None))

        result = await self.session.execute(query)
        return result.scalar_one()

    async def get_by_campaign(
        self,
        campaign_id: UUID,
        policy_type: Optional[PolicyType] = None,
        active_only: bool = True
    ) -> List[Policy]:
        """Retrieve policies for a campaign."""
        query = select(PolicyDB).where(
            PolicyDB.campaign_id == campaign_id,
            PolicyDB.deleted_at.is_(None)
        )

        if policy_type:
            query = query.where(PolicyDB.policy_type == PolicyTypeEnum(policy_type.value))

        if active_only:
            query = query.where(PolicyDB.is_active == True)  # noqa: E712

        query = query.order_by(desc(PolicyDB.version))

        result = await self.session.execute(query)
        db_policies = result.scalars().all()
        return [self._to_domain(db_p) for db_p in db_policies]

    async def get_active_policy(
        self,
        campaign_id: UUID,
        policy_type: PolicyType
    ) -> Optional[Policy]:
        """Get the active policy of a specific type for a campaign."""
        result = await self.session.execute(
            select(PolicyDB).where(
                PolicyDB.campaign_id == campaign_id,
                PolicyDB.policy_type == PolicyTypeEnum(policy_type.value),
                PolicyDB.is_active == True,  # noqa: E712
                PolicyDB.deleted_at.is_(None)
            ).order_by(desc(PolicyDB.version))
            .limit(1)
        )
        db_policy = result.scalar_one_or_none()
        return self._to_domain(db_policy) if db_policy else None

    async def get_latest_version(
        self,
        campaign_id: UUID,
        policy_name: str,
        policy_type: PolicyType
    ) -> Optional[Policy]:
        """Get the latest version of a policy."""
        result = await self.session.execute(
            select(PolicyDB).where(
                PolicyDB.campaign_id == campaign_id,
                PolicyDB.name == policy_name,
                PolicyDB.policy_type == PolicyTypeEnum(policy_type.value),
                PolicyDB.deleted_at.is_(None)
            ).order_by(desc(PolicyDB.version))
            .limit(1)
        )
        db_policy = result.scalar_one_or_none()
        return self._to_domain(db_policy) if db_policy else None

    @staticmethod
    def _to_domain(db_policy: PolicyDB) -> Policy:
        """Convert database model to domain model."""
        return Policy(
            id=db_policy.id,
            campaign_id=db_policy.campaign_id,
            name=db_policy.name,
            policy_type=PolicyType(db_policy.policy_type.value),
            version=db_policy.version,
            config=db_policy.config,
            is_active=db_policy.is_active,
            created_at=db_policy.created_at,
            updated_at=db_policy.updated_at,
            deleted_at=db_policy.deleted_at,
        )
