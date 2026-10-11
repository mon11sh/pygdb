"""
Accounts Service - Utility Helpers

Helper functions for account number generation and other utilities.

Author: GDB Architecture Team
"""

import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


class AccountNumberGenerator:
    """
    Generator for account numbers with sequence management.
    
    Account numbers start from 1000 and increment by 1.
    Pattern: 1000, 1001, 1002, etc.
    """
    
    START_NUMBER = 1000
    
    @staticmethod
    def format_account_number(seq_value: int) -> int:
        """
        Format sequence value to account number.
        
        Since we're using BIGSERIAL starting from 1, we need to convert it.
        Using the sequence starting from 1000 directly.
        
        Args:
            seq_value: Sequence value from database
            
        Returns:
            Formatted account number (starting from 1000)
        """
        # If sequence is already set to start from 1000, use directly
        return seq_value
    
    @staticmethod
    def is_valid_account_number(account_number: int) -> bool:
        """
        Validate if account number is in valid range.
        
        Valid account numbers: >= 1000
        
        Args:
            account_number: Account number to validate
            
        Returns:
            True if valid, False otherwise
        """
        return account_number >= AccountNumberGenerator.START_NUMBER


def generate_idempotency_key() -> str:
    """
    Generate a unique idempotency key for transaction safety.
    
    Used for at-most-once semantics in debit/credit operations.
    Prevents duplicate transactions on retry.
    
    Returns:
        Unique idempotency key (UUID v4 format)
    """
    return str(uuid.uuid4())


def get_transaction_id() -> str:
    """
    Generate a unique transaction ID.
    
    Used for tracking transactions across services.
    
    Returns:
        Unique transaction ID
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    unique_id = str(uuid.uuid4())[:8]
    return f"{timestamp}-{unique_id}"


def mask_account_number(account_number: int) -> str:
    """
    Mask account number for logging/display.
    
    Shows only last 4 digits: XXXX1234
    
    Args:
        account_number: Account number to mask
        
    Returns:
        Masked account number string
    """
    account_str = str(account_number)
    if len(account_str) <= 4:
        return "XXXX"
    return "X" * (len(account_str) - 4) + account_str[-4:]


def mask_phone_number(phone_number: str) -> str:
    """
    Mask phone number for logging/display.
    
    Shows only last 4 digits: XXXXXX1234
    
    Args:
        phone_number: Phone number to mask
        
    Returns:
        Masked phone number string
    """
    if len(phone_number) <= 4:
        return "X" * len(phone_number)
    return "X" * (len(phone_number) - 4) + phone_number[-4:]


def mask_pin(pin: str) -> str:
    """
    Mask PIN for logging/display.
    
    Shows only last character: XXXX
    
    Args:
        pin: PIN to mask
        
    Returns:
        Masked PIN string (all X's)
    """
    return "X" * len(pin)


class ResponseFormatter:
    """Format API responses consistently."""
    
    @staticmethod
    def success_response(data: dict, message: str = "Success") -> dict:
        """
        Format a success response.
        
        Args:
            data: Response data
            message: Success message
            
        Returns:
            Formatted response
        """
        return {
            "status": "SUCCESS",
            "message": message,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def error_response(error_code: str, message: str, details: dict = None) -> dict:
        """
        Format an error response.
        
        Args:
            error_code: Machine-readable error code
            message: Human-readable error message
            details: Additional error details
            
        Returns:
            Formatted error response
        """
        response = {
            "status": "ERROR",
            "error_code": error_code,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if details:
            response["details"] = details
            
        return response
