"""Payment processing error for the transactions service.

Defines :class:`PaymentProcessingError`, raised when the downstream payment
gateway rejects or fails to process a transaction during a deposit, withdrawal,
or transfer. Part of the transactions_service exception hierarchy rooted at
:class:`TransactionException`.
"""
from .transaction_exception import TransactionException

class PaymentProcessingError(TransactionException):
    """Raised when the payment gateway rejects or fails a transaction.

    Signals that money movement could not be completed because the external
    payment processor declined the request. Maps to HTTP 400 with error code
    ``PAYMENT_GATEWAY_ERROR``.
    """
    def __init__(self, message="Payment Gateway Rejected Transaction"):
        """Initialize the payment processing error.

        Args:
            message: Human-readable description of the gateway rejection.
        """
        super().__init__(
            message=message,
            error_code="PAYMENT_GATEWAY_ERROR",
            http_code=400
        )
