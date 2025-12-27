"""
Variant domain model - represents a candidate solution in the evolution process.

CRITICAL: This model implements lineage tracking, which is a non-negotiable invariant.
Every variant must track its parent and generation number.
"""

import hashlib
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, computed_field


class Variant(BaseModel):
    """
    Variant entity - represents a single variant in the evolution process.

    Domain Invariants:
    1. Every variant (except generation 0) must have a parent_id
    2. Generation number must increment from parent
    3. Content hash must be unique and deterministic
    4. Mutation metadata must be recorded for traceability
    """

    id: UUID = Field(default_factory=uuid4)
    round_id: UUID
    parent_id: Optional[UUID] = None
    generation: int = Field(ge=0, description="Generation number (0 for initial population)")
    content: str = Field(min_length=1, description="The actual prompt/variant content")
    mutation_type: Optional[str] = Field(
        None,
        description="Type of mutation applied (e.g., 'crossover', 'mutation', 'initial')"
    )
    mutation_metadata: dict = Field(
        default_factory=dict,
        description="Metadata about how this variant was created"
    )
    is_selected: bool = Field(default=False, description="Selected for next round")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None

    @computed_field  # type: ignore[misc]
    @property
    def content_hash(self) -> str:
        """
        Generate deterministic SHA-256 hash of content.
        Used for deduplication and tracking identical variants.
        """
        return hashlib.sha256(self.content.encode('utf-8')).hexdigest()

    @classmethod
    def create_initial(
        cls,
        round_id: UUID,
        content: str,
        metadata: Optional[dict] = None,
    ) -> "Variant":
        """
        Create an initial variant (generation 0, no parent).

        Args:
            round_id: The round this variant belongs to
            content: The variant content
            metadata: Optional metadata about creation

        Returns:
            Variant instance with generation=0, no parent
        """
        return cls(
            round_id=round_id,
            parent_id=None,
            generation=0,
            content=content,
            mutation_type="initial",
            mutation_metadata=metadata or {},
        )

    @classmethod
    def create_from_parent(
        cls,
        parent: "Variant",
        round_id: UUID,
        content: str,
        mutation_type: str,
        mutation_metadata: Optional[dict] = None,
    ) -> "Variant":
        """
        Create a new variant from a parent variant.

        Enforces lineage invariant: child.generation = parent.generation + 1

        Args:
            parent: The parent variant
            round_id: The round this variant belongs to
            content: The new variant content
            mutation_type: Type of mutation applied
            mutation_metadata: Metadata about the mutation

        Returns:
            Variant instance with incremented generation and parent link
        """
        return cls(
            round_id=round_id,
            parent_id=parent.id,
            generation=parent.generation + 1,
            content=content,
            mutation_type=mutation_type,
            mutation_metadata=mutation_metadata or {},
        )

    def select_for_next_round(self) -> None:
        """Mark this variant as selected for the next generation."""
        self.is_selected = True
        self.updated_at = datetime.utcnow()

    def soft_delete(self) -> None:
        """Soft delete this variant (for audit trail)."""
        self.deleted_at = datetime.utcnow()

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "round_id": "660e8400-e29b-41d4-a716-446655440001",
                    "parent_id": None,
                    "generation": 0,
                    "content": "You are a helpful assistant.",
                    "mutation_type": "initial",
                    "mutation_metadata": {},
                    "is_selected": False,
                }
            ]
        }
    }
