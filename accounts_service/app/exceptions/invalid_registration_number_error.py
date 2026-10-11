"""Exception raised when a company registration number is invalid.

Defines :class:`InvalidRegistrationNumberError`, a domain error signalling
that a supplied company registration number failed validation. Part of the
accounts service exception hierarchy rooted at :class:`AccountException`.
"""
from .account_exception import AccountException

class InvalidRegistrationNumberError(AccountException):
    """Raised when company registration validation fails."""
    
    def __init__(self, registration_no: str, message: str = "Invalid company registration number"):
        """Build the error combining the message and the offending number.

        Args:
            registration_no: The registration number that failed validation.
            message: Optional description prefixed to the number.
        """
        super().__init__(
            f"{message}: {registration_no}",
            "INVALID_REGISTRATION_NUMBER"
        )
