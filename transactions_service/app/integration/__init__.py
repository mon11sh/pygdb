"""Integration clients for the transactions service.

Houses the outbound HTTP clients used to talk to the other microservices this
service depends on: the account service (balance/PIN/debit/credit), the central
payment gateway (second-level transfer validation), and the notification service.
"""
# Package initialization
