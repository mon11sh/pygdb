"""Validation package for the transactions service.

Groups the stateless validators that enforce transaction invariants -- amount
bounds, sufficient balance, PIN format, transfer limits, and same-account
guards -- before any money movement is attempted.
"""
# Package initialization
