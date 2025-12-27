"""Unit tests for Variant domain model."""

from uuid import uuid4

import pytest

from evo_ai.domain.models.variant import Variant


class TestVariant:
    """Test cases for Variant entity."""

    def test_create_initial_variant(self):
        """Test creating an initial variant (generation 0)."""
        round_id = uuid4()
        content = "You are a helpful assistant."

        variant = Variant.create_initial(
            round_id=round_id,
            content=content,
            metadata={"source": "manual"}
        )

        assert variant.round_id == round_id
        assert variant.parent_id is None
        assert variant.generation == 0
        assert variant.content == content
        assert variant.mutation_type == "initial"
        assert variant.mutation_metadata == {"source": "manual"}
        assert variant.is_selected is False

    def test_create_from_parent(self):
        """Test creating a variant from a parent."""
        round_id = uuid4()
        parent = Variant.create_initial(
            round_id=round_id,
            content="Original prompt"
        )

        child = Variant.create_from_parent(
            parent=parent,
            round_id=round_id,
            content="Modified prompt",
            mutation_type="mutation",
            mutation_metadata={"change": "added emphasis"}
        )

        # Verify lineage tracking
        assert child.parent_id == parent.id
        assert child.generation == parent.generation + 1
        assert child.generation == 1
        assert child.content == "Modified prompt"
        assert child.mutation_type == "mutation"

    def test_lineage_tracking_multiple_generations(self):
        """Test lineage tracking across multiple generations."""
        round_id = uuid4()

        # Generation 0
        gen0 = Variant.create_initial(round_id=round_id, content="Gen 0")
        assert gen0.generation == 0
        assert gen0.parent_id is None

        # Generation 1
        gen1 = Variant.create_from_parent(
            parent=gen0,
            round_id=round_id,
            content="Gen 1",
            mutation_type="mutation"
        )
        assert gen1.generation == 1
        assert gen1.parent_id == gen0.id

        # Generation 2
        gen2 = Variant.create_from_parent(
            parent=gen1,
            round_id=round_id,
            content="Gen 2",
            mutation_type="crossover"
        )
        assert gen2.generation == 2
        assert gen2.parent_id == gen1.id

    def test_content_hash_generation(self):
        """Test that content hash is generated automatically."""
        variant = Variant.create_initial(
            round_id=uuid4(),
            content="Test content"
        )

        assert variant.content_hash is not None
        assert len(variant.content_hash) == 64  # SHA-256 produces 64 hex characters

    def test_content_hash_deterministic(self):
        """Test that identical content produces identical hash."""
        content = "Identical content"
        variant1 = Variant.create_initial(round_id=uuid4(), content=content)
        variant2 = Variant.create_initial(round_id=uuid4(), content=content)

        assert variant1.content_hash == variant2.content_hash

    def test_content_hash_different_for_different_content(self):
        """Test that different content produces different hash."""
        variant1 = Variant.create_initial(round_id=uuid4(), content="Content A")
        variant2 = Variant.create_initial(round_id=uuid4(), content="Content B")

        assert variant1.content_hash != variant2.content_hash

    def test_select_for_next_round(self):
        """Test marking variant as selected."""
        variant = Variant.create_initial(round_id=uuid4(), content="Test")

        assert variant.is_selected is False

        variant.select_for_next_round()

        assert variant.is_selected is True

    def test_soft_delete(self):
        """Test soft deletion of variant."""
        variant = Variant.create_initial(round_id=uuid4(), content="Test")

        assert variant.deleted_at is None

        variant.soft_delete()

        assert variant.deleted_at is not None
