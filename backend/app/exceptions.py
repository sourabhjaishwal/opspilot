class IncidentNotFoundError(Exception):
    """Raised when an incident cannot be found."""


class ServiceNotFoundError(Exception):
    """Raised when a service cannot be found."""


class ServiceNameAlreadyExistsError(Exception):
    """Raised when a service name is already registered."""
