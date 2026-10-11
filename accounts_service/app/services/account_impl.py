"""
Account Implementation Interface

Abstract base class defining the contract for account type implementations.
Each account type must implement the open() method with its specific business rules.

Author: GDB Architecture Team
"""

from abc import ABC, abstractmethod
from typing import Union
from app.models.account import SavingsAccountCreate, CurrentAccountCreate


class AccountImpl(ABC):
    """
    Abstract interface for account type implementations.
    
    Each concrete implementation handles account-type-specific:
    - Validation rules
    - Business logic
    - Account creation
    """
    
    @abstractmethod
    async def open(
        self,
        account_data: Union[SavingsAccountCreate, CurrentAccountCreate],
        pin_hash: str
    ) -> int:
        """
        Open a new account with type-specific business rules.
        
        Args:
            account_data: Account creation data (type-specific)
            pin_hash: Hashed PIN for the account
            
        Returns:
            Account number of the created account
            
        Raises:
            ValidationError: If validation fails
            DuplicateConstraintError: If unique constraints violated
            AgeRestrictionError: If age requirements not met (Savings)
        """
        pass
