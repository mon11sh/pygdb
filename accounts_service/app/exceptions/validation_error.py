"""Exception raised when field-level validation fails.

Defines :class:`ValidationError`, a domain error signalling that a specific
input field failed validation, capturing both the field name and the
reason. Part of the accounts service exception hierarchy rooted at
:class:`AccountException`.
"""
from .account_exception import AccountException

class ValidationError(AccountException):
    """Raised when validation fails."""
    
    def __init__(self, field: str, message: str):
        """Build the error identifying the invalid field and the reason.

        Args:
            field: Name of the field that failed validation.
            message: Description of why the field is invalid.
        """
        super().__init__(
            f"Validation error in {field}: {message}",
            "VALIDATION_ERROR"
        )
