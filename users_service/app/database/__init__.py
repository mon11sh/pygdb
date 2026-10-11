"""Database package for the users microservice.

Provides the provider-agnostic database bootstrap, the portable SQLAlchemy ORM
models, shared seed data, and the pluggable provider implementations selected at
runtime by settings.DATABASE_PROVIDER.
"""
