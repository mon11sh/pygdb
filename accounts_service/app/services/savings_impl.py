"""
Savings Account Implementation

Concrete implementation of AccountImpl for Savings accounts.
Encapsulates all Savings-specific business rules and validations.

Author: GDB Architecture Team
"""

import logging
from app.services.account_impl import AccountImpl
from app.models.account import SavingsAccountCreate
from app.repositories.account_repo import AccountRepository
from app.utils.validators import (
    validate_age,
    validate_pin,
    validate_phone_number,
    validate_name,
    validate_privilege
)
from app.integration.aadhar_client import AadharClient
from app.exceptions.account_exceptions import ValidationError
from app.utils.compliance_logger import compliance_logger
from app.integration.notification_client import NotificationClient

logger = logging.getLogger(__name__)

# 14. Hardcoded blacklist for demonstration (requirement says "no table")
BLACKLISTED_AADHAR = {"999999999999", "888888888888"}
BLACKLISTED_NAMES = {"Fake User", "Scammer John"}


class SavingsImpl(AccountImpl):
    """
    Savings Account implementation.
    
    Business Rules:
    - Minimum age: 18 years
    - Requires: Name, DOB, PIN, Phone Number, Aadhar Number
    - Unique constraint: Name + DOB combination
    - Phone number must be valid Indian format
    - Aadhar number must be verified with UIDAI
    """
    
    def __init__(self):
        """Initialize with repository access from the active provider."""
        from app.database.connection import get_provider
        self.repo = get_provider().account_repository()
    
    async def open(
        self,
        account_data: SavingsAccountCreate,
        pin_hash: str
    ) -> int:
        """
        Open a new Savings account.
        
        Validates:
        - Age >= 18
        - Valid DOB format
        - Valid PIN
        - Valid phone number (Indian format)
        - Unique name + DOB combination
        - Valid privilege level
        - Valid Aadhar number (verified with UIDAI)
        
        Args:
            account_data: Savings account creation data
            pin_hash: Hashed PIN
            
        Returns:
            Account number
            
        Raises:
            AgeRestrictionError: If age < 18
            ValidationError: If validation fails
            DuplicateConstraintError: If name+DOB exists
        """
        logger.info(f"Opening Savings account for: {account_data.name}")
        
        # Savings-specific validations
        validate_name(account_data.name)
        validate_age(account_data.date_of_birth, min_age=18)
        validate_pin(account_data.pin)
        validate_phone_number(account_data.phone_no, country="IN")
        validate_privilege(account_data.privilege)
        
        # 14. Check if blacklisted
        if account_data.aadhar_number in BLACKLISTED_AADHAR or account_data.name in BLACKLISTED_NAMES:
            logger.warning(f"❌ Account creation rejected: {account_data.name} is blacklisted")
            raise ValidationError("account", "Account holder is blacklisted")

        # 4. Check if Aadhar already has an active account
        if await self.repo.check_aadhar_has_active_account(account_data.aadhar_number):
            logger.warning(f"❌ Aadhar {account_data.aadhar_number} already has an active account")
            raise ValidationError("aadhar_number", "An active account already exists for this Aadhar number")
        
        # Verify Aadhar number with third-party service
        logger.info(f"Verifying Aadhar number: {account_data.aadhar_number[:4]}********")
        try:
            from app.exceptions.invalid_aadhar_number_error import InvalidAadharNumberError
            
            aadhar_response = await AadharClient.verify_aadhar(account_data.aadhar_number)
            
            if not aadhar_response.get("is_valid", False):
                error_msg = aadhar_response.get("message", "Invalid Aadhar number")
                logger.error(f"❌ Aadhar verification failed: {error_msg}")
                
                # Send notification for invalid Aadhar
                await NotificationClient.send_notification(
                    user_id=account_data.phone_no,
                    message=f"Account opening failed: The provided Aadhar number {account_data.aadhar_number[:4]}... is invalid. {error_msg}",
                    notification_type="ERROR"
                )
                
                raise InvalidAadharNumberError(account_data.aadhar_number, error_msg)
            
            logger.info(f"✅ Aadhar number verified successfully")
            
        except ValueError as e:
            # Validation error from Aadhar service
            logger.error(f"❌ Aadhar validation error: {e}")
            raise InvalidAadharNumberError(account_data.aadhar_number, str(e))
        except InvalidAadharNumberError:
            # Re-raise known exception as-is
            raise
        except Exception as e:
            # Service unavailable or other errors
            logger.error(f"❌ Aadhar verification service error: {e}")
            raise ValidationError("aadhar_number", f"Unable to verify Aadhar number: {str(e)}")
        
        # Create account via repository
        account_number = await self.repo.create_savings_account(
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
            message=f"Welcome {account_data.name}! Your Savings account {account_number} is now active.",
            notification_type="SUCCESS",
            mode="WELCOME"
        )
        
        logger.info(f"✅ Savings account created: {account_number}")
        return account_number

