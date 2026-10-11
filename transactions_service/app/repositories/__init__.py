"""Repositories package for the transactions service.

Groups the provider-agnostic data-access contracts (transaction, transaction
log, transfer limit, idempotency) together with their concrete asyncpg,
SQLAlchemy, and in-memory implementations. Callers depend on the interfaces so
the active persistence backend can be swapped without touching service code.
"""

# Package initialization
