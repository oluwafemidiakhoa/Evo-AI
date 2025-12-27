"""Domain-specific exceptions."""


class DomainException(Exception):
    """Base exception for all domain errors."""

    pass


class EntityNotFoundError(DomainException):
    """Raised when an entity is not found."""

    def __init__(self, entity_type: str, entity_id: str):
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} with ID {entity_id} not found")


class InvalidStateTransitionError(DomainException):
    """Raised when attempting an invalid state transition."""

    def __init__(self, entity_type: str, current_state: str, attempted_action: str):
        self.entity_type = entity_type
        self.current_state = current_state
        self.attempted_action = attempted_action
        super().__init__(
            f"Cannot {attempted_action} {entity_type} with status {current_state}"
        )


class LineageViolationError(DomainException):
    """Raised when variant lineage invariant is violated."""

    def __init__(self, message: str):
        super().__init__(f"Lineage invariant violation: {message}")


class DuplicateContentError(DomainException):
    """Raised when duplicate variant content is detected."""

    def __init__(self, content_hash: str):
        self.content_hash = content_hash
        super().__init__(f"Variant with content hash {content_hash} already exists")


class ConcurrencyError(DomainException):
    """Raised when optimistic locking detects concurrent modification."""

    def __init__(self, entity_type: str, entity_id: str):
        super().__init__(
            f"{entity_type} {entity_id} was modified by another process"
        )


class InvariantViolationError(DomainException):
    """Raised when a domain invariant is violated."""

    def __init__(self, message: str):
        super().__init__(f"Domain invariant violation: {message}")
