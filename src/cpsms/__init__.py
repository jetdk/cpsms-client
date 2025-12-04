"""
CPSMS - Python client for the CPSMS.dk SMS Gateway API.

A simple, typed Python client with both synchronous and asynchronous support.

Example:
    >>> from cpsms import CPSMSClient
    >>> with CPSMSClient(username="user", api_key="key") as client:
    ...     result = client.send_sms(to="4512345678", message="Hello!", from_="MyApp")
    ...     print(f"Sent! Cost: {result.success[0].cost}")

    >>> from cpsms import AsyncCPSMSClient
    >>> async with AsyncCPSMSClient(username="user", api_key="key") as client:
    ...     result = await client.send_sms(to="4512345678", message="Hello!", from_="MyApp")
"""

from cpsms.client import AsyncCPSMSClient, CPSMSClient
from cpsms.exceptions import (
    AuthenticationError,
    BadRequestError,
    ConflictError,
    CPSMSError,
    ForbiddenError,
    InsufficientCreditError,
    NotFoundError,
)
from cpsms.models import (
    Contact,
    DeliveryStatus,
    Group,
    LogEntry,
    SendResponse,
    SMSError,
    SMSFormat,
    SMSResult,
)

__version__ = "1.0.0"
__author__ = "Jerome Thorstenson"
__email__ = "jetdk81@gmail.com"

__all__ = [
    # Clients
    "CPSMSClient",
    "AsyncCPSMSClient",
    # Models
    "SMSFormat",
    "DeliveryStatus",
    "SMSResult",
    "SMSError",
    "SendResponse",
    "Group",
    "Contact",
    "LogEntry",
    # Exceptions
    "CPSMSError",
    "AuthenticationError",
    "InsufficientCreditError",
    "ForbiddenError",
    "NotFoundError",
    "ConflictError",
    "BadRequestError",
]
