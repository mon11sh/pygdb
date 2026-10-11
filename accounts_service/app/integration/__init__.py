"""Integration package for the accounts service.

Groups the outbound HTTP clients that let the accounts service talk to other
microservices in the platform: Aadhaar verification, Company (CRV) registration
verification, and the central Notification service. Service and route code
depends on these clients rather than issuing raw HTTP calls itself.
"""
# Integration package
