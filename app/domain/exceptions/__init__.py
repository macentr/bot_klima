"""Domain exceptions."""


class DomainError(Exception):
    """Base domain error."""


class NotFoundError(DomainError):
    """Entity not found."""


class ConflictError(DomainError):
    """Uniqueness/invariant conflict."""


class AccessDeniedError(DomainError):
    """RBAC violation."""

