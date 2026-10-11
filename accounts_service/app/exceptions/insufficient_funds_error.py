"""Exception raised when an account has insufficient funds.

Defines :class:`InsufficientFundsError`, a domain error signalling that a
transaction cannot proceed because the available balance is below the
required amount. Part of the accounts service exception hierarchy rooted
at :class:`AccountException`.
"""
from .account_exception import AccountException

class InsufficientFundsError(AccountException):
    """Raised when account balance is insufficient for transaction."""
    
    def __init__(self, balance: float, required: float):
        """Build the error reporting available balance versus requirement.

        Args:
            balance: Current available balance on the account.
            required: Amount required to complete the transaction.
        """
        super().__init__(
            f"Insufficient funds. Balance: ₹{balance}, Required: ₹{required}",
            "INSUFFICIENT_FUNDS"
        )
