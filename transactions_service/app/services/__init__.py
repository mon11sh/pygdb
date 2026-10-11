"""Service layer for the transactions microservice.

Aggregates the money-movement and reporting services that orchestrate the
transaction flow: deposits, withdrawals, and transfers (with idempotency-key
reserve/complete/release guards), plus transfer-limit enforcement and
transaction-log querying. Each service coordinates repositories and external
service clients (Account, Payment Gateway, Notification) on behalf of the API
routers.
"""

# Package initialization
