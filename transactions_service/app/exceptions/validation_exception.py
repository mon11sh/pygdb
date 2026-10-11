"""Validation exception for the transactions service.

Defines :class:`ValidationException`, raised when a money-movement request fails
input validation (e.g., malformed or out-of-range fields). Part of the
transactions_service exception hierarchy rooted at :class:`TransactionException`.
"""
from .transaction_exception import TransactionException

class ValidationException(TransactionException):
    """Input validation failed."""
    
    http_code = 422
    error_code = "VALIDATION_ERROR"
