"""Database package for the accounts service.

Groups the provider-agnostic bootstrap (``connection``/``db``), the portable
SQLAlchemy ORM models, the shared seed data, and the pluggable storage providers
under ``providers/``. The active backend is chosen at runtime from
settings.DATABASE_PROVIDER.
"""

# Database Package
