"""
Accounts Service - Validation Utilities

Helper functions for account validation.

Author: GDB Architecture Team
"""

import re
from datetime import datetime
from dateutil.relativedelta import relativedelta

from app.exceptions.account_exceptions import (
    AgeRestrictionError,
    ValidationError,
    InvalidPinError
)


def validate_age(date_of_birth: str, min_age: int = 18) -> int:
    """
    Validate age from DOB.
    
    Args:
        date_of_birth: DOB in YYYY-MM-DD format
        min_age: Minimum required age (default 18)
        
    Returns:
        Age in years
        
    Raises:
        AgeRestrictionError: If age is less than min_age
        ValidationError: If DOB format is invalid
    """
    try:
        dob = datetime.strptime(date_of_birth, "%Y-%m-%d").date()
        today = datetime.now().date()
        age = relativedelta(today, dob).years
        
        if age < min_age:
            raise AgeRestrictionError(age)
        
        return age
        
    except ValueError as e:
        raise ValidationError("date_of_birth", "Invalid date format. Use YYYY-MM-DD")


def validate_pin(pin: str) -> str:
    """
    Validate PIN format.
    
    Rules:
    - Must be 4-6 digits
    - Cannot be all same digits (1111, 22222, etc.)
    - Cannot be purely sequential consecutive digits (1234, 43210, etc.)
    
    Args:
        pin: PIN string
        
    Returns:
        Valid PIN
        
    Raises:
        InvalidPinError: If PIN is invalid
    """
    # Check length - must be between 4 and 6 digits
    if not (4 <= len(pin) <= 6):
        raise InvalidPinError("PIN must be between 4 and 6 digits")
    
    # Check if numeric
    if not pin.isdigit():
        raise InvalidPinError("PIN must contain only digits")
    
    # Check for all same digits
    if len(set(pin)) == 1:
        raise InvalidPinError("PIN cannot have all identical digits")
    
    # Check for purely sequential consecutive digits
    # Only reject if each digit differs by exactly 1 from the next
    digits = [int(d) for d in pin]
    
    # Check ascending: 0123, 1234, 2345, etc.
    is_ascending_sequential = all(digits[i+1] - digits[i] == 1 for i in range(len(digits)-1))
    
    # Check descending: 3210, 4321, 5432, etc.
    is_descending_sequential = all(digits[i] - digits[i+1] == 1 for i in range(len(digits)-1))
    
    if is_ascending_sequential or is_descending_sequential:
        raise InvalidPinError("PIN cannot be purely sequential (like 1234 or 4321)")
    
    return pin


def validate_phone_number(phone: str, country: str = "IN") -> str:
    """
    Validate phone number.
    
    Args:
        phone: Phone number string
        country: Country code (default IN for India)
        
    Returns:
        Valid phone number
        
    Raises:
        ValidationError: If phone is invalid
    """
    if country == "IN":
        # Indian phone: 10 digits
        if not re.match(r"^\d{10}$", phone):
            raise ValidationError("phone_no", "Indian phone must be 10 digits")
    
    return phone


def validate_email(email: str) -> str:
    """
    Validate email address.
    
    Args:
        email: Email string
        
    Returns:
        Valid email
        
    Raises:
        ValidationError: If email is invalid
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    
    if not re.match(pattern, email):
        raise ValidationError("email", "Invalid email format")
    
    return email


def validate_name(name: str) -> str:
    """
    Validate account holder name.
    
    Rules:
    - 1-255 characters
    - Can contain letters, spaces, hyphens, apostrophes
    
    Args:
        name: Name string
        
    Returns:
        Valid name
        
    Raises:
        ValidationError: If name is invalid
    """
    if not (2 <= len(name) <= 255):
        raise ValidationError("name", "Name must be 2-255 characters")
    
    if not re.match(r"^[a-zA-Z\s\-']+$", name):
        raise ValidationError("name", "Name can only contain letters, spaces, hyphens, and apostrophes")
    
    return name


def validate_company_name(company: str) -> str:
    """
    Validate company name.
    
    Args:
        company: Company name string
        
    Returns:
        Valid company name
        
    Raises:
        ValidationError: If company name is invalid
    """
    if not (1 <= len(company) <= 255):
        raise ValidationError("company_name", "Company name must be 1-255 characters")
    
    return company


def validate_registration_number(reg_no: str) -> str:
    """
    Validate company registration number.
    
    Args:
        reg_no: Registration number
        
    Returns:
        Valid registration number
        
    Raises:
        ValidationError: If registration number is invalid
    """
    if not (1 <= len(reg_no) <= 50):
        raise ValidationError("registration_no", "Registration number must be 1-50 characters")
    
    return reg_no


def validate_privilege(privilege: str) -> str:
    """
    Validate privilege level.
    
    Args:
        privilege: Privilege level
        
    Returns:
        Valid privilege
        
    Raises:
        ValidationError: If privilege is invalid
    """
    valid_privileges = ["PREMIUM", "GOLD", "SILVER"]
    
    if privilege not in valid_privileges:
        raise ValidationError("privilege", f"Privilege must be one of: {', '.join(valid_privileges)}")
    
    return privilege
