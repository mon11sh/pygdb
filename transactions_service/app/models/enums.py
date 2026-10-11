"""
Enums for Transaction Service

Defines enumeration types for:
- Transaction types (WITHDRAW, DEPOSIT, TRANSFER)
- Transfer modes (NEFT, RTGS, IMPS, UPI, CHEQUE)
- Privilege levels (PREMIUM, GOLD, SILVER)
"""

from enum import Enum


class TransactionType(str, Enum):
    """Types of transactions."""
    WITHDRAWAL = "WITHDRAW"
    DEPOSIT = "DEPOSIT"
    TRANSFER = "TRANSFER"


class TransferMode(str, Enum):
    """Transfer modes (banking standards)."""
    NEFT = "NEFT"       # National Electronic Funds Transfer
    RTGS = "RTGS"       # Real Time Gross Settlement
    IMPS = "IMPS"       # Immediate Payment Service
    UPI = "UPI"         # Unified Payments Interface
    CHEQUE = "CHEQUE"   # Cheque payment


class PrivilegeLevel(str, Enum):
    """Account privilege levels (determines transfer limits)."""
    PREMIUM = "PREMIUM"    # Highest transaction limits
    GOLD = "GOLD"          # Standard transaction limits
    SILVER = "SILVER"      # Basic transaction limits
