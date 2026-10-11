"""Unauthorized exception for the transactions service.

Defines :class:`UnauthorizedException`, raised when a caller lacks valid
authentication (e.g., missing or invalid credentials) for a money-movement
operation. Part of the transactions_service exception hierarchy rooted at
:class:`TransactionException`.
"""
from .transaction_exception import TransactionException

class UnauthorizedException(TransactionException):
    """User is not authorized for this operation."""
    
    http_code = 401
    error_code = "UNAUTHORIZED"
