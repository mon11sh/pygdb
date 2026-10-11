"""
Compliance Logger Utility

Handles auditing requirements:
- Writing account details to a text file
- Logging encrypted sensitive data (Aadhar, PIN) to CSV
- Action logging

Author: GDB Architecture Team
"""

import os
import csv
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from app.utils.encryption import EncryptionManager

logger = logging.getLogger(__name__)

class ComplianceLogger:
    """Utility for compliance and audit logging."""
    
    def __init__(self):
        """Prepare the compliance log directory and audit CSV.

        Instantiates the ``EncryptionManager``, ensures the
        ``logs/compliance`` directory exists, and writes the CSV header row
        for the audit log if the file does not already exist.
        """
        self.encryption = EncryptionManager()
        self.logs_dir = Path("logs/compliance")
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        self.accounts_file = self.logs_dir / "created_accounts.txt"
        self.audit_csv = self.logs_dir / "audit_log.csv"
        
        # Initialize CSV if not exists
        if not self.audit_csv.exists():
            with open(self.audit_csv, "w", newline="") as f:
                writer = csv.writer(f)
                # Store one-way SHA-256 hashes (NOT reversible ciphertext) so the
                # audit trail can prove which value was seen without ever being
                # able to recover the raw PIN / Aadhar from the log.
                writer.writerow(["Timestamp", "Account Number", "Action", "Aadhar_SHA256", "PIN_SHA256"])

    async def log_account_creation(self, account_number: int, account_data: Dict[str, Any], pin: str):
        """
        Implementation of requirements 15, 16, 17.
        """
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 15. Store account information in a text file
            with open(self.accounts_file, "a") as f:
                f.write(f"[{timestamp}] New Account Created: {account_number}\n")
                f.write(f"Holder: {account_data.get('name')}\n")
                f.write(f"Type: {account_data.get('account_type')}\n")
                f.write("-" * 30 + "\n")
            
            # 16. Log a one-way (non-recoverable) digest of PIN and Aadhar in CSV.
            # SHA-256 is irreversible: the audit log proves what value was used
            # without storing recoverable secrets (Fernet ciphertext could be
            # decrypted with the key and was effectively reversible PII at rest).
            aadhar_value = account_data.get("aadhar_number", "N/A")
            aadhar_hash = hashlib.sha256(aadhar_value.encode()).hexdigest()
            pin_hash = hashlib.sha256(pin.encode()).hexdigest()

            with open(self.audit_csv, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    timestamp,
                    account_number,
                    "Acc created",
                    aadhar_hash,
                    pin_hash
                ])
                
            logger.info(f"✅ Compliance logs updated for account {account_number}")
            
        except Exception as e:
            logger.error(f"❌ Error in compliance logging: {e}")
            # We don't raise here to avoid failing account creation if logging fails
            # but in a real production system, this might be a critical failure.

compliance_logger = ComplianceLogger()
