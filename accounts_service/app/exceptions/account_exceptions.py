"""Central aggregation of the accounts service exception hierarchy.

Re-exports every custom domain exception from a single module so that
service, repository, and API layers can import all account-related errors
from one place. Each exception ultimately derives from
:class:`AccountException` and pairs a message with an error code.
"""
from .account_exception import AccountException
from .account_not_found_error import AccountNotFoundError
from .account_already_exists_error import AccountAlreadyExistsError
from .account_inactive_error import AccountInactiveError
from .account_closed_error import AccountClosedError
from .insufficient_funds_error import InsufficientFundsError
from .invalid_balance_error import InvalidBalanceError
from .invalid_account_type_error import InvalidAccountTypeError
from .invalid_privilege_error import InvalidPrivilegeError
from .invalid_pin_error import InvalidPinError
from .age_restriction_error import AgeRestrictionError
from .validation_error import ValidationError
from .operation_not_allowed_error import OperationNotAllowedError
from .database_error import DatabaseError
from .concurrency_error import ConcurrencyError
from .duplicate_constraint_error import DuplicateConstraintError
from .account_already_active_error import AccountAlreadyActiveError
from .account_already_inactive_error import AccountAlreadyInactiveError
from .invalid_registration_number_error import InvalidRegistrationNumberError
from .invalid_aadhar_number_error import InvalidAadharNumberError
