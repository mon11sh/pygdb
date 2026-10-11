"""Database package for the transactions service.

Bundles the provider-agnostic bootstrap (``db``), the portable SQLAlchemy ORM
models, the shared seed data, and the pluggable ``providers`` package. The rest
of the service reaches storage exclusively through the active database provider.
"""

# Package initialization
