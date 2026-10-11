"""
Notification Domain Models.

Defines the data structures exchanged by the notification service, including the
enumeration of supported notification severities and the validated request model
used when submitting a notification. Field-level constraints bound untrusted
input at the API edge as defense-in-depth against abuse and stored-XSS.

Author: GDB Architecture Team
"""

from pydantic.dataclasses import dataclass
from pydantic import Field
from enum import Enum
from typing import Optional

class NotificationType(str, Enum):
    """Enumerate the supported notification severity categories.

    Members double as their string values, allowing the type to be serialized
    directly to and from JSON while constraining callers to a known set.
    """
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"

@dataclass
class NotificationRequest:
    """Validated payload describing a notification to be delivered.

    Captures the recipient, message body, severity type, and optional title and
    delivery mode. Length constraints on the recipient, message, and title bound
    untrusted fields at the edge; HTML escaping of the message is performed later
    in the storage layer before persistence.
    """
    # Bound the untrusted fields at the edge (stored-XSS / abuse defense-in-depth).
    # Angle-bracket escaping happens in the storage layer before persistence.
    recipient: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1, max_length=2000)
    type: NotificationType = NotificationType.INFO
    title: Optional[str] = Field(default=None, max_length=255)
    mode: Optional[str] = Field(default=None, max_length=50)
