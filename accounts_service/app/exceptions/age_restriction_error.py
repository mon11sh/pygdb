"""Exception raised when an account holder is below the minimum age.

Defines :class:`AgeRestrictionError`, a domain error signalling that the
account holder does not meet the minimum age requirement (18 years). Part
of the accounts service exception hierarchy rooted at
:class:`AccountException`.
"""
from .account_exception import AccountException

class AgeRestrictionError(AccountException):
    """Raised when account holder is underage."""
    
    def __init__(self, age: int):
        """Build the error stating the minimum age and the current age.

        Args:
            age: The account holder's current age that failed the check.
        """
        super().__init__(
            f"Account holder must be at least 18 years old (Current age: {age})",
            "AGE_RESTRICTION"
        )
