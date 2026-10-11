"""Exception raised when an idempotency key is reused in conflict.

Defines :class:`IdempotencyException`, a domain exception in the
transactions_service exception hierarchy. It is raised when an idempotency key
is replayed with a request that conflicts with the original, preventing
duplicate money movement, mapping to an HTTP 409 Conflict response.
"""
from .transaction_exception import TransactionException

class IdempotencyException(TransactionException):
    """Idempotency key violation."""
    
    http_code = 409
    error_code = "IDEMPOTENCY_CONFLICT"
