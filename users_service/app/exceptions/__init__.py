"""Exceptions package for the user management service.

Aggregates the custom, domain-specific exception hierarchy used throughout the
users service. Every exception derives from ``UserManagementException`` (an
``HTTPException`` subclass), pairing an HTTP status code with a stable
machine-readable ``error_code`` for consistent client-side error handling.
"""

# Exceptions Package
