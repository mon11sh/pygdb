"""Exception raised when a persistence operation fails.

Defines :class:`DatabaseException`, a domain exception in the
transactions_service exception hierarchy. It is raised when a database
operation backing a money-movement action (reads, writes, or commits) fails,
mapping to an HTTP 500 Internal Server Error response.
"""
from .transaction_exception import TransactionException

class DatabaseException(TransactionException):
    """Database operation failed."""
    
    http_code = 500
    error_code = "DATABASE_ERROR"
