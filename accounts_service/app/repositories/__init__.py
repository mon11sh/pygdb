"""Repositories package for the accounts service.

Holds the provider-agnostic data-access layer: the abstract AccountRepository
contract plus its concrete implementations (SQLAlchemy for SQL providers and an
in-memory store). Services and dependency-injection depend on the abstraction
here, never on a specific database driver.
"""
# Repositories Package
