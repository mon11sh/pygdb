"""
Account Factory

Factory class for creating account type implementations.
Provides a single point for instantiating the correct AccountImpl based on account type.

Author: GDB Architecture Team
"""

import logging
from typing import Dict, Type
from app.services.account_impl import AccountImpl
from app.services.savings_impl import SavingsImpl
from app.services.current_impl import CurrentImpl
from app.exceptions.account_exceptions import ValidationError

logger = logging.getLogger(__name__)


class AccountFactory:
    """
    Factory for creating account type implementations.
    
    Follows the Factory pattern to:
    - Centralize account type creation logic
    - Enable easy addition of new account types
    - Maintain Open/Closed Principle (open for extension, closed for modification)
    """
    
    # Registry of account types to their implementations
    _implementations: Dict[str, Type[AccountImpl]] = {
        'SAVINGS': SavingsImpl,
        'CURRENT': CurrentImpl,
    }
    
    @classmethod
    def create(cls, account_type: str) -> AccountImpl:
        """
        Create and return the appropriate AccountImpl for the given type.
        
        Args:
            account_type: Type of account ('SAVINGS' or 'CURRENT')
            
        Returns:
            Concrete AccountImpl instance
            
        Raises:
            ValidationError: If account_type is not supported
            
        Example:
            >>> factory = AccountFactory()
            >>> savings_impl = factory.create('SAVINGS')
            >>> account_num = await savings_impl.open(account_data, pin_hash)
        """
        account_type_upper = account_type.upper()
        
        impl_class = cls._implementations.get(account_type_upper)
        
        if not impl_class:
            supported_types = ', '.join(cls._implementations.keys())
            raise ValidationError(
                f"Unsupported account type: {account_type}. "
                f"Supported types: {supported_types}"
            )
        
        logger.debug(f"Creating {account_type_upper} account implementation")
        return impl_class()
    
    @classmethod
    def register_account_type(
        cls,
        account_type: str,
        implementation: Type[AccountImpl]
    ) -> None:
        """
        Register a new account type implementation.
        
        Allows runtime extension of supported account types without modifying factory code.
        
        Args:
            account_type: Name of the account type (e.g., 'FIXED_DEPOSIT')
            implementation: Class implementing AccountImpl
            
        Example:
            >>> AccountFactory.register_account_type('FIXED_DEPOSIT', FixedDepositImpl)
        """
        cls._implementations[account_type.upper()] = implementation
        logger.info(f"✅ Registered new account type: {account_type.upper()}")
    
    @classmethod
    def get_supported_types(cls) -> list[str]:
        """
        Get list of currently supported account types.
        
        Returns:
            List of supported account type names
        """
        return list(cls._implementations.keys())
