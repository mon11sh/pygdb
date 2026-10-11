"""Aggregated re-exports of the authentication exception hierarchy.

Provides a single convenient import location for every custom exception
used by the auth service, spanning credential, token, user-state, and
infrastructure (database / dependent service / internal) failures.
"""
from .authentication_exception import AuthenticationException
from .invalid_credentials_exception import InvalidCredentialsException
from .user_inactive_exception import UserInactiveException
from .user_not_found_exception import UserNotFoundException
from .token_expired_exception import TokenExpiredException
from .invalid_token_exception import InvalidTokenException
from .token_revoked_exception import TokenRevokedException
from .service_unavailable_exception import ServiceUnavailableException
from .database_exception import DatabaseException
from .internal_server_exception import InternalServerException
