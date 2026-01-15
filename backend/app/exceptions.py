"""Custom exceptions for the STM Intelligence Brief System."""

from typing import Any, Dict, Optional


class AppException(Exception):
    """Base exception for application errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(AppException):
    """Raised when input validation fails."""

    def __init__(self, message: str, field: Optional[str] = None):
        details = {"field": field} if field else {}
        super().__init__(message, status_code=400, details=details)


class NotFoundError(AppException):
    """Raised when a requested resource is not found."""

    def __init__(self, resource: str, resource_id: Any):
        message = f"{resource} with id '{resource_id}' not found"
        super().__init__(message, status_code=404, details={"resource": resource, "id": str(resource_id)})


class UnauthorizedError(AppException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, status_code=401)


class ForbiddenError(AppException):
    """Raised when user lacks permission."""

    def __init__(self, message: str = "Permission denied"):
        super().__init__(message, status_code=403)


class ConflictError(AppException):
    """Raised when there's a resource conflict (e.g., duplicate)."""

    def __init__(self, message: str):
        super().__init__(message, status_code=409)


class RateLimitError(AppException):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded. Please try again later."):
        super().__init__(message, status_code=429)


class DatabaseError(AppException):
    """Raised when a database operation fails."""

    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message, status_code=500)
