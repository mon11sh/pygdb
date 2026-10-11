"""Service layer package for the Accounts microservice.

Houses the business-logic services that sit between the API routers and the
repository layer: the account creation Factory/Interface hierarchy
(``account_factory``, ``account_impl``, ``savings_impl``, ``current_impl``),
the high-level ``account_service`` orchestrator, and the ``internal_service``
used for service-to-service calls.
"""
# Services Package
