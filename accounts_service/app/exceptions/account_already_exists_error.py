"""Exception raised when creating an account that already exists.

Defines :class:`AccountAlreadyExistsError`, a domain error signalling that
an account with the same identity (name, optionally date of birth) is
already present. Part of the accounts service exception hierarchy rooted
at :class:`AccountException`.
"""
from .account_exception import AccountException

class AccountAlreadyExistsError(AccountException):
    """Raised when account already exists."""
    
    def __init__(self, name: str, dob: str = None):
        """Build the error, optionally including the date of birth.

        Args:
            name: Name of the account holder that already exists.
            dob: Optional date of birth appended to the message when given.
        """
        msg = f"Account with name '{name}'"
        if dob:
            msg += f" and DOB '{dob}'"
        msg += " already exists"
        super().__init__(msg, "ACCOUNT_ALREADY_EXISTS")
