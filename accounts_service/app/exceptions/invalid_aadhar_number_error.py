"""Exception raised when an Aadhaar number fails validation.

Defines :class:`InvalidAadharNumberError`, a domain error signalling that a
supplied Aadhaar identifier is malformed or otherwise invalid. Part of the
accounts service exception hierarchy rooted at :class:`AccountException`.
"""
from .account_exception import AccountException

class InvalidAadharNumberError(AccountException):
    """Raised when Aadhar number validation fails."""
    
    def __init__(self, aadhar_number: str, message: str = "Invalid Aadhar number"):
        """Build the error combining the message and the offending number.

        Args:
            aadhar_number: The Aadhaar number that failed validation.
            message: Optional description prefixed to the number.
        """
        super().__init__(
            f"{message}: {aadhar_number}",
            "INVALID_AADHAR_NUMBER"
        )
