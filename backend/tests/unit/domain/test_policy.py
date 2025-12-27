"""Unit tests for Policy domain model."""

from uuid import uuid4

from evo_ai.domain.models.policy import Policy, PolicyType


class TestPolicy:
    """Test cases for Policy entity."""

    def test_create_policy(self):
        """Test creating a policy."""
        campaign_id = uuid4()
        policy = Policy(
            campaign_id=campaign_id,
            name="Top-K Selection",
            policy_type=PolicyType.SELECTION,
            config={"strategy": "top_k", "k": 5}
        )

        assert policy.campaign_id == campaign_id
        assert policy.name == "Top-K Selection"
        assert policy.policy_type == PolicyType.SELECTION
        assert policy.version == 1
        assert policy.is_active is True

    def test_activate_policy(self):
        """Test activating a policy."""
        campaign_id = uuid4()
        policy = Policy(
            campaign_id=campaign_id,
            name="Test Policy",
            policy_type=PolicyType.SELECTION,
            config={}
        )
        policy.deactivate()

        policy.activate()

        assert policy.is_active is True

    def test_deactivate_policy(self):
        """Test deactivating a policy."""
        campaign_id = uuid4()
        policy = Policy(
            campaign_id=campaign_id,
            name="Test Policy",
            policy_type=PolicyType.SELECTION,
            config={}
        )

        policy.deactivate()

        assert policy.is_active is False

    def test_create_new_version(self):
        """Test creating a new version of a policy."""
        campaign_id = uuid4()
        policy_v1 = Policy(
            campaign_id=campaign_id,
            name="Test Policy",
            policy_type=PolicyType.SELECTION,
            version=1,
            config={"param": "value1"}
        )

        policy_v2 = policy_v1.create_new_version(
            new_config={"param": "value2", "new_param": "value3"}
        )

        assert policy_v2.campaign_id == policy_v1.campaign_id
        assert policy_v2.name == policy_v1.name
        assert policy_v2.policy_type == policy_v1.policy_type
        assert policy_v2.version == 2
        assert policy_v2.config["param"] == "value2"
        assert policy_v2.config["new_param"] == "value3"
        assert policy_v2.is_active is True

    def test_policy_types(self):
        """Test different policy types."""
        campaign_id = uuid4()

        selection_policy = Policy(
            campaign_id=campaign_id,
            name="Selection",
            policy_type=PolicyType.SELECTION,
            config={}
        )
        assert selection_policy.policy_type == PolicyType.SELECTION

        mutation_policy = Policy(
            campaign_id=campaign_id,
            name="Mutation",
            policy_type=PolicyType.MUTATION,
            config={}
        )
        assert mutation_policy.policy_type == PolicyType.MUTATION

        termination_policy = Policy(
            campaign_id=campaign_id,
            name="Termination",
            policy_type=PolicyType.TERMINATION,
            config={}
        )
        assert termination_policy.policy_type == PolicyType.TERMINATION

    def test_soft_delete(self):
        """Test soft deletion of policy."""
        campaign_id = uuid4()
        policy = Policy(
            campaign_id=campaign_id,
            name="Test Policy",
            policy_type=PolicyType.SELECTION,
            config={}
        )

        assert policy.deleted_at is None

        policy.soft_delete()

        assert policy.deleted_at is not None
