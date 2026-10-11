"""Configuration package for the transactions service.

Exposes the pydantic ``Settings`` object (database provider selection,
inter-service URLs, JWT/security, transfer limits, and business rules) that the
rest of the service imports for runtime configuration.
"""
# Package initialization
