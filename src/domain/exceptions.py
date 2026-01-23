"""Domain-specific exceptions."""


class DomainError(Exception):
    """Base domain exception."""

    pass


# Alias for backward compatibility
DomainException = DomainError


class InvalidStateTransition(DomainException):
    """Invalid state machine transition."""

    pass


class InvalidPlan(DomainException):
    """Plan validation failed."""

    pass


class SessionNotFound(DomainException):
    """Session does not exist."""

    pass


class ProfileNotFound(DomainException):
    """User profile not found."""

    pass


class QuestionValidationError(DomainException):
    """Question validation failed."""

    pass


class LLMError(DomainException):
    """LLM-related errors."""

    pass


class StorageError(DomainException):
    """Storage-related errors."""

    pass


class SetupRequiredError(Exception):
    """Raised when first-time setup is needed.

    This is not a DomainException because it's a configuration/setup issue,
    not a business logic error.
    """

    pass


# Alias for backward compatibility
SetupRequired = SetupRequiredError
