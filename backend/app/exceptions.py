class IncidentNotFoundError(Exception):
    """Raised when an incident cannot be found."""


class ServiceNotFoundError(Exception):
    """Raised when a service cannot be found."""


class ServiceNameAlreadyExistsError(Exception):
    """Raised when a service name is already registered."""


class AIServiceConfigError(Exception):
    """Raised when AI service configuration is missing or invalid."""


class AIServiceError(Exception):
    """Raised when the AI service encounters an error or fails to produce a valid response."""
