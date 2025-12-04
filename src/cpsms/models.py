"""Data models for the CPSMS API client."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class SMSFormat(str, Enum):
    """SMS encoding format.

    Attributes:
        GSM: Standard format - 160 chars per SMS (153 if multipart).
        UNICODE: For special characters (Chinese, emojis, etc.) -
                 70 chars per SMS (67 if multipart).
    """
    GSM = "GSM"
    UNICODE = "UNICODE"


class DeliveryStatus(int, Enum):
    """Delivery report status codes.

    These are the status values sent to your dlr_url webhook.

    Attributes:
        SUCCESSFUL: Message delivered successfully.
        FAILED: Message delivery failed.
        BUFFERED: Message is buffered for later delivery.
        ABANDONED: Message delivery was abandoned.
    """
    SUCCESSFUL = 1
    FAILED = 2
    BUFFERED = 4
    ABANDONED = 8


@dataclass
class SMSResult:
    """Result of sending an SMS to a single recipient.

    Attributes:
        to: The recipient phone number.
        cost: The cost in SMS points.
        sms_amount: Number of SMS segments used.
    """
    to: str
    cost: float
    sms_amount: int = 1


@dataclass
class SMSError:
    """Error when sending an SMS to a recipient.

    Attributes:
        code: Error code from the API.
        message: Human-readable error message.
        to: The recipient phone number (if applicable).
    """
    code: int
    message: str
    to: str | None = None


@dataclass
class SendResponse:
    """Response from sending SMS.

    Contains both successful sends and any errors that occurred.

    Attributes:
        success: List of successfully sent messages.
        errors: List of failed messages with error details.
    """
    success: list[SMSResult]
    errors: list[SMSError]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SendResponse:
        """Parse API response into SendResponse.

        Args:
            data: Raw JSON response from the API.

        Returns:
            Parsed SendResponse object.
        """
        success = []
        errors = []

        if "success" in data:
            success_data = data["success"]
            if isinstance(success_data, list):
                for item in success_data:
                    success.append(SMSResult(
                        to=item["to"],
                        cost=item.get("cost", 0),
                        sms_amount=item.get("smsAmount", 1)
                    ))
            elif isinstance(success_data, dict):
                success.append(SMSResult(
                    to=success_data["to"],
                    cost=success_data.get("cost", 0),
                    sms_amount=success_data.get("smsAmount", 1)
                ))

        if "error" in data:
            error_data = data["error"]
            if isinstance(error_data, list):
                for item in error_data:
                    errors.append(SMSError(
                        code=item.get("code", 0),
                        message=item.get("message", ""),
                        to=item.get("to")
                    ))
            elif isinstance(error_data, dict):
                errors.append(SMSError(
                    code=error_data.get("code", 0),
                    message=error_data.get("message", ""),
                    to=error_data.get("to")
                ))

        return cls(success=success, errors=errors)


@dataclass
class Group:
    """SMS contact group.

    Attributes:
        group_id: Unique identifier for the group.
        group_name: Display name of the group.
    """
    group_id: int
    group_name: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Group:
        """Parse API response into Group.

        Args:
            data: Raw JSON response from the API.

        Returns:
            Parsed Group object.
        """
        return cls(
            group_id=int(data["groupId"]),
            group_name=data["groupName"]
        )


@dataclass
class Contact:
    """SMS contact.

    Attributes:
        phone_number: Phone number with country code.
        contact_name: Optional display name.
        time_added: When the contact was added to the group.
    """
    phone_number: str
    contact_name: str | None = None
    time_added: datetime | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Contact:
        """Parse API response into Contact.

        Args:
            data: Raw JSON response from the API.

        Returns:
            Parsed Contact object.
        """
        time_added = None
        if "timeAdded" in data:
            time_added = datetime.fromtimestamp(data["timeAdded"])
        return cls(
            phone_number=data["phoneNumber"],
            contact_name=data.get("contactName"),
            time_added=time_added
        )


@dataclass
class LogEntry:
    """SMS log entry.

    Attributes:
        to: Recipient phone number.
        from_: Sender name/number.
        sms_amount: Number of SMS segments.
        point_price: Cost in SMS points.
        user_reference: Your custom reference (if set).
        dlr_status: Delivery status code.
        dlr_status_text: Human-readable delivery status.
        time_sent: When the SMS was sent.
    """
    to: str
    from_: str
    sms_amount: int
    point_price: float
    user_reference: str | None
    dlr_status: int
    dlr_status_text: str
    time_sent: datetime

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LogEntry:
        """Parse API response into LogEntry.

        Args:
            data: Raw JSON response from the API.

        Returns:
            Parsed LogEntry object.
        """
        return cls(
            to=data["to"],
            from_=data["from"],
            sms_amount=data["smsAmount"],
            point_price=data["pointPrice"],
            user_reference=data.get("userReference"),
            dlr_status=data["dlrStatus"],
            dlr_status_text=data.get("dlrStatusText", ""),
            time_sent=datetime.fromtimestamp(data["timeSent"])
        )
