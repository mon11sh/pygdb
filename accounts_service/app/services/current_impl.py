"""
Current Account Implementation

Concrete implementation of AccountImpl for Current accounts.
Encapsulates all Current-specific business rules and validations.

Author: GDB Architecture Team
"""

import logging
from app.services.account_impl import AccountImpl
from app.models.account import CurrentAccountCreate
from app.repositories.account_repo import AccountRepository
from app.utils.validators import (
    validate_pin,
    validate_name,
    validate_company_name,
    validate_registration_number,
    validate_privilege
)
from app.utils.compliance_logger import compliance_logger
from app.integration.notification_client import NotificationClient

logger = logging.getLogger(__name__)

# 14. Hardcoded blacklist for demonstration
BLACKLISTED_NAMES = {"Fake User", "Scammer John"}


class CurrentImpl(AccountImpl):
    """
    Current Account implementation.
    
    Business Rules:
    - No age restriction (business accounts)
    - Requires: Name, Company Name, Registration Number, PIN
    - Unique constraint: Registration Number
    - Company name must be valid
    """
    
    def __init__(self):
        """Initialize with repository access from the active provider."""
        from app.database.connection import get_provider
        self.repo = get_provider().account_repository()
    
    async def open(
        self,
        account_data: CurrentAccountCreate,
        pin_hash: str
    ) -> int:
        """
        Open a new Current account.
        
        Validates:
        - Valid PIN
        - Valid company name
        - Valid registration number
        - Unique registration number
        - Valid privilege level
        
        Args:
            account_data: Current account creation data
            pin_hash: Hashed PIN
            
        Returns:
            Account number
            
        Raises:
            ValidationError: If validation fails
            DuplicateConstraintError: If registration_no exists
        """
        logger.info(f"Opening Current account for: {account_data.company_name}")
        
        # Current-specific validations
        # Validate PIN, name, company name, registration number format
        validate_name(account_data.name)
        validate_pin(account_data.pin)
        validate_company_name(account_data.company_name)
        validate_registration_number(account_data.registration_no)
        validate_privilege(account_data.privilege)
        
        # 14. Check if blacklisted
        if account_data.name in BLACKLISTED_NAMES:
            logger.warning(f"❌ Account creation rejected: {account_data.name} is blacklisted")
            raise ValidationError("account", "Account holder is blacklisted")
        
        # Verify Registration Number with third-party service
        logger.info(f"Verifying Registration Number: {account_data.registration_no[:8]}*************")
        try:
            from app.integration.company_client import CompanyClient
            from app.exceptions.invalid_registration_number_error import InvalidRegistrationNumberError
            from app.exceptions.validation_error import ValidationError
            
            company_response = await CompanyClient.verify_registration(account_data.registration_no)
            
            if not company_response.get("is_valid", False):
                error_msg = company_response.get("message", "Invalid Registration Number")
                logger.error(f"❌ Company verification failed: {error_msg}")
                
                # Send notification for invalid Registration Number
                # Using name as fallback user_id since no phone available in basic Current data
                await NotificationClient.send_notification(
                    user_id=account_data.name,
                    message=f"Current Account opening failed: The Registration Number {account_data.registration_no[:4]}... is invalid. {error_msg}",
                    notification_type="ERROR"
                )
                
                raise InvalidRegistrationNumberError(account_data.registration_no, error_msg)
            
            logger.info(f"✅ Company Registration Number verified successfully")
            
        except ValueError as e:
            # Validation error from Company service
            logger.error(f"❌ Company validation error: {e}")
            raise InvalidRegistrationNumberError(account_data.registration_no, str(e))
        except InvalidRegistrationNumberError:
            # Re-raise known exception as-is
            raise
        except Exception as e:
            # Service unavailable or other errors
            logger.error(f"❌ Company verification service error: {e}")
            raise ValidationError("registration_no", f"Unable to verify Registration Number: {str(e)}")
        
        # Create account via repository
        account_number = await self.repo.create_current_account(
            account_data,
            pin_hash
        )
        
        # 15, 16, 17. Compliance logging
        await compliance_logger.log_account_creation(
            account_number, 
            account_data.model_dump(), 
            account_data.pin
        )
        
        # 18. Send notification
        await NotificationClient.send_notification(
            user_id=str(account_number),
            message=f"Welcome {account_data.company_name}! Your Current account {account_number} is now active.",
            notification_type="SUCCESS",
            mode="WELCOME"
        )
        
        logger.info(f"✅ Current account created: {account_number}")
        return account_number
