"""Synchronous and asynchronous clients for the CPSMS API."""

from __future__ import annotations

import base64
from datetime import datetime
from typing import Any

import httpx

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
    Group,
    LogEntry,
    SendResponse,
    SMSFormat,
)


def _raise_for_error(response: httpx.Response) -> None:
    """Raise appropriate exception for error responses."""
    if response.status_code == 200:
        return

    try:
        data = response.json()
        error_msg = data.get("error", {}).get("message", response.text)
    except Exception:
        error_msg = response.text

    error_classes = {
        400: BadRequestError,
        401: AuthenticationError,
        402: InsufficientCreditError,
        403: ForbiddenError,
        404: NotFoundError,
        409: ConflictError,
    }

    error_class = error_classes.get(response.status_code, CPSMSError)
    raise error_class(response.status_code, error_msg)


class CPSMSClientBase:
    """Base class with shared functionality for CPSMS clients."""

    BASE_URL = "https://api.cpsms.dk/v2"

    def __init__(self, username: str, api_key: str, timeout: float = 30.0):
        """
        Initialize CPSMS client.

        Args:
            username: Your CPSMS username.
            api_key: Your generated API key from CPSMS dashboard
                     (Settings -> API).
            timeout: Request timeout in seconds.
        """
        self.username = username
        self.api_key = api_key
        self.timeout = timeout
        self._auth_header = self._create_auth_header()

    def _create_auth_header(self) -> str:
        """Create Basic Auth header value."""
        credentials = f"{self.username}:{self.api_key}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    @property
    def _headers(self) -> dict[str, str]:
        """Default headers for API requests."""
        return {
            "Authorization": self._auth_header,
            "Content-Type": "application/json",
        }

    def _build_send_payload(
        self,
        to: str | list[str],
        message: str,
        from_: str | None = None,
        timestamp: int | datetime | None = None,
        encoding: str | None = None,
        dlr_url: str | None = None,
        flash: bool = False,
        reference: str | None = None,
        format_: SMSFormat | None = None,
    ) -> dict[str, Any]:
        """Build payload for send SMS endpoint."""
        payload: dict[str, Any] = {
            "to": to,
            "message": message,
        }

        if from_:
            payload["from"] = from_

        if timestamp:
            if isinstance(timestamp, datetime):
                payload["timestamp"] = int(timestamp.timestamp())
            else:
                payload["timestamp"] = timestamp

        if encoding:
            payload["encoding"] = encoding

        if dlr_url:
            payload["dlr_url"] = dlr_url

        if flash:
            payload["flash"] = 1

        if reference:
            payload["reference"] = reference

        if format_:
            payload["format"] = format_.value

        return payload

    def _build_send_group_payload(
        self,
        to_group: int,
        message: str,
        from_: str | None = None,
        timestamp: int | datetime | None = None,
        encoding: str | None = None,
        dlr_url: str | None = None,
        flash: bool = False,
    ) -> dict[str, Any]:
        """Build payload for send to group endpoint."""
        payload: dict[str, Any] = {
            "to_group": to_group,
            "message": message,
        }

        if from_:
            payload["from"] = from_

        if timestamp:
            if isinstance(timestamp, datetime):
                payload["timestamp"] = int(timestamp.timestamp())
            else:
                payload["timestamp"] = timestamp

        if encoding:
            payload["encoding"] = encoding

        if dlr_url:
            payload["dlr_url"] = dlr_url

        if flash:
            payload["flash"] = 1

        return payload


class CPSMSClient(CPSMSClientBase):
    """
    Synchronous CPSMS API client.

    Example:
        >>> with CPSMSClient(username="myuser", api_key="my-api-key") as client:
        ...     result = client.send_sms(
        ...         to="4512345678",
        ...         message="Hello from Python!",
        ...         from_="MyApp"
        ...     )
        ...     print(f"Cost: {result.success[0].cost}")

        >>> # Or without context manager
        >>> client = CPSMSClient(username="myuser", api_key="my-api-key")
        >>> credit = client.get_credit()
        >>> client.close()
    """

    def __init__(self, username: str, api_key: str, timeout: float = 30.0):
        super().__init__(username, api_key, timeout)
        self._client = httpx.Client(timeout=timeout)

    def __enter__(self) -> CPSMSClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def close(self) -> None:
        """Close the HTTP client and release resources."""
        self._client.close()

    def _request(
        self,
        method: str,
        endpoint: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Make HTTP request to API."""
        url = f"{self.BASE_URL}/{endpoint}"
        response = self._client.request(
            method=method,
            url=url,
            headers=self._headers,
            json=json,
            params=params,
        )
        _raise_for_error(response)
        return response

    # ==================== SMS Methods ====================

    def send_sms(
        self,
        to: str | list[str],
        message: str,
        from_: str | None = None,
        timestamp: int | datetime | None = None,
        encoding: str | None = None,
        dlr_url: str | None = None,
        flash: bool = False,
        reference: str | None = None,
        format_: SMSFormat | None = None,
    ) -> SendResponse:
        """
        Send SMS to one or multiple recipients.

        Args:
            to: Phone number(s) with country code (e.g., "4512345678").
            message: SMS text (max 1530 characters).
            from_: Sender name - alphanumeric (max 11 chars) or
                   numeric (max 15 chars).
            timestamp: Schedule send time as Unix timestamp or datetime.
            encoding: Character encoding - "UTF-8" (default) or "ISO-8859-1".
            dlr_url: Webhook URL for delivery reports.
            flash: If True, send as flash SMS (displays immediately on screen).
            reference: Your reference for the message (max 32 chars).
                      Required if you want to cancel the SMS later.
            format_: SMSFormat.GSM (default) or SMSFormat.UNICODE for
                    special characters.

        Returns:
            SendResponse containing success and error details.

        Raises:
            InsufficientCreditError: Not enough SMS credits.
            BadRequestError: Invalid parameters.
            AuthenticationError: Invalid credentials.
        """
        payload = self._build_send_payload(
            to=to,
            message=message,
            from_=from_,
            timestamp=timestamp,
            encoding=encoding,
            dlr_url=dlr_url,
            flash=flash,
            reference=reference,
            format_=format_,
        )
        response = self._request("POST", "send", json=payload)
        return SendResponse.from_dict(response.json())

    def send_to_group(
        self,
        to_group: int,
        message: str,
        from_: str | None = None,
        timestamp: int | datetime | None = None,
        encoding: str | None = None,
        dlr_url: str | None = None,
        flash: bool = False,
    ) -> SendResponse:
        """
        Send SMS to all contacts in a group.

        Args:
            to_group: Group ID to send to.
            message: SMS text (max 1530 characters).
            from_: Sender name.
            timestamp: Schedule send time.
            encoding: Character encoding.
            dlr_url: Webhook URL for delivery reports.
            flash: If True, send as flash SMS.

        Returns:
            SendResponse containing success and error details.
        """
        payload = self._build_send_group_payload(
            to_group=to_group,
            message=message,
            from_=from_,
            timestamp=timestamp,
            encoding=encoding,
            dlr_url=dlr_url,
            flash=flash,
        )
        response = self._request("POST", "sendgroup", json=payload)
        return SendResponse.from_dict(response.json())

    def get_credit(self) -> str:
        """
        Get remaining SMS credit balance.

        Returns:
            Credit balance as formatted string (e.g., "9.843,40").
        """
        response = self._request("GET", "creditvalue")
        credit: str = response.json()["credit"]
        return credit

    def delete_sms(self, reference: str) -> bool:
        """
        Delete/cancel a scheduled SMS by reference.

        The SMS must be scheduled at least 10 minutes in the future.

        Args:
            reference: The reference you set when sending the SMS.

        Returns:
            True if deleted successfully.

        Raises:
            ConflictError: SMS not found or too close to send time.
        """
        payload = {"reference": reference}
        self._request("DELETE", "deletesms", json=payload)
        return True

    # ==================== Group Methods ====================

    def create_group(self, group_name: str) -> Group:
        """
        Create a new contact group.

        Args:
            group_name: Display name for the group.

        Returns:
            The created Group object with its ID.
        """
        payload = {"groupName": group_name}
        response = self._request("POST", "addgroup", json=payload)
        data = response.json()["success"]
        return Group.from_dict(data)

    def list_groups(self) -> list[Group]:
        """
        List all contact groups.

        Returns:
            List of Group objects.
        """
        response = self._request("GET", "listgroups")
        data = response.json()
        if isinstance(data, list):
            return [Group.from_dict(g) for g in data]
        return []

    def update_group(self, group_id: int, group_name: str) -> bool:
        """
        Update a group's name.

        Args:
            group_id: ID of the group to update.
            group_name: New name for the group.

        Returns:
            True if updated successfully.
        """
        payload = {"groupId": group_id, "groupName": group_name}
        self._request("PUT", "updategroup", json=payload)
        return True

    def delete_group(self, group_id: int) -> bool:
        """
        Delete a group.

        The group must be empty (no contacts) to be deleted.

        Args:
            group_id: ID of the group to delete.

        Returns:
            True if deleted successfully.

        Raises:
            ConflictError: Group is not empty.
        """
        payload = {"groupId": group_id}
        self._request("DELETE", "deletegroup", json=payload)
        return True

    # ==================== Contact Methods ====================

    def create_contact(
        self,
        group_id: int,
        phone_number: str,
        contact_name: str | None = None,
    ) -> bool:
        """
        Create a contact or add existing contact to a group.

        If the contact already exists in another group, it will be
        added to this group as well.

        Args:
            group_id: ID of the group to add the contact to.
            phone_number: Phone number with country code.
            contact_name: Optional display name for the contact.

        Returns:
            True if created/added successfully.
        """
        payload: dict[str, Any] = {
            "groupId": group_id,
            "phoneNumber": phone_number,
        }
        if contact_name:
            payload["contactName"] = contact_name

        self._request("POST", "addcontact", json=payload)
        return True

    def list_contacts(self, group_id: int) -> list[Contact]:
        """
        List all contacts in a group.

        Args:
            group_id: ID of the group.

        Returns:
            List of Contact objects.
        """
        response = self._request("GET", f"listcontacts/{group_id}")
        data = response.json()
        if isinstance(data, list):
            return [Contact.from_dict(c) for c in data]
        return []

    def update_contact(
        self,
        group_id: int,
        phone_number: str,
        contact_name: str,
    ) -> bool:
        """
        Update a contact's name.

        Args:
            group_id: ID of the group containing the contact.
            phone_number: Phone number of the contact to update.
            contact_name: New name for the contact.

        Returns:
            True if updated successfully.
        """
        payload = {
            "groupId": group_id,
            "phoneNumber": phone_number,
            "contactName": contact_name,
        }
        self._request("PUT", "updatecontact", json=payload)
        return True

    def delete_contact(self, group_id: int, phone_number: str) -> bool:
        """
        Remove a contact from a group.

        If the contact is removed from all groups, it will be
        completely deleted.

        Args:
            group_id: ID of the group to remove the contact from.
            phone_number: Phone number of the contact to remove.

        Returns:
            True if deleted/removed successfully.
        """
        payload = {
            "groupId": group_id,
            "phoneNumber": phone_number,
        }
        self._request("DELETE", "deletecontact", json=payload)
        return True

    def list_group_membership(self, phone_number: str) -> list[Group]:
        """
        List all groups a contact belongs to.

        Args:
            phone_number: Phone number of the contact.

        Returns:
            List of Group objects the contact is a member of.
        """
        response = self._request("GET", f"listgroupmembership/{phone_number}")
        data = response.json().get("success", [])

        if isinstance(data, dict):
            return [Group.from_dict(data)]
        elif isinstance(data, list):
            return [Group.from_dict(g) for g in data]
        return []

    # ==================== Log Methods ====================

    def get_log(
        self,
        to: str | None = None,
        from_date: int | datetime | None = None,
        to_date: int | datetime | None = None,
    ) -> list[LogEntry]:
        """
        Get SMS log entries.

        Can look back a maximum of 3 months from current time.

        Args:
            to: Filter by recipient phone number.
            from_date: Start date for log entries.
            to_date: End date for log entries.

        Returns:
            List of LogEntry objects.
        """
        params: dict[str, Any] = {}

        if to:
            params["to"] = to

        if from_date:
            if isinstance(from_date, datetime):
                params["fromDate"] = int(from_date.timestamp())
            else:
                params["fromDate"] = from_date

        if to_date:
            if isinstance(to_date, datetime):
                params["toDate"] = int(to_date.timestamp())
            else:
                params["toDate"] = to_date

        response = self._request("GET", "getlog", params=params if params else None)
        data = response.json()

        if isinstance(data, list):
            return [LogEntry.from_dict(entry) for entry in data]
        return []


class AsyncCPSMSClient(CPSMSClientBase):
    """
    Asynchronous CPSMS API client.

    Example:
        >>> async with AsyncCPSMSClient(username="myuser", api_key="key") as client:
        ...     result = await client.send_sms(
        ...         to="4512345678",
        ...         message="Hello from Python!",
        ...         from_="MyApp"
        ...     )

        >>> # Send to multiple recipients concurrently
        >>> async with AsyncCPSMSClient(username="myuser", api_key="key") as client:
        ...     tasks = [
        ...         client.send_sms(to=num, message="Hello!", from_="MyApp")
        ...         for num in ["4512345678", "4587654321"]
        ...     ]
        ...     results = await asyncio.gather(*tasks)
    """

    def __init__(self, username: str, api_key: str, timeout: float = 30.0):
        super().__init__(username, api_key, timeout)
        self._client = httpx.AsyncClient(timeout=timeout)

    async def __aenter__(self) -> AsyncCPSMSClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def close(self) -> None:
        """Close the HTTP client and release resources."""
        await self._client.aclose()

    async def _request(
        self,
        method: str,
        endpoint: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Make async HTTP request to API."""
        url = f"{self.BASE_URL}/{endpoint}"
        response = await self._client.request(
            method=method,
            url=url,
            headers=self._headers,
            json=json,
            params=params,
        )
        _raise_for_error(response)
        return response

    # ==================== SMS Methods ====================

    async def send_sms(
        self,
        to: str | list[str],
        message: str,
        from_: str | None = None,
        timestamp: int | datetime | None = None,
        encoding: str | None = None,
        dlr_url: str | None = None,
        flash: bool = False,
        reference: str | None = None,
        format_: SMSFormat | None = None,
    ) -> SendResponse:
        """
        Send SMS to one or multiple recipients.

        Args:
            to: Phone number(s) with country code (e.g., "4512345678").
            message: SMS text (max 1530 characters).
            from_: Sender name - alphanumeric (max 11 chars) or
                   numeric (max 15 chars).
            timestamp: Schedule send time as Unix timestamp or datetime.
            encoding: Character encoding - "UTF-8" (default) or "ISO-8859-1".
            dlr_url: Webhook URL for delivery reports.
            flash: If True, send as flash SMS (displays immediately on screen).
            reference: Your reference for the message (max 32 chars).
            format_: SMSFormat.GSM (default) or SMSFormat.UNICODE.

        Returns:
            SendResponse containing success and error details.
        """
        payload = self._build_send_payload(
            to=to,
            message=message,
            from_=from_,
            timestamp=timestamp,
            encoding=encoding,
            dlr_url=dlr_url,
            flash=flash,
            reference=reference,
            format_=format_,
        )
        response = await self._request("POST", "send", json=payload)
        return SendResponse.from_dict(response.json())

    async def send_to_group(
        self,
        to_group: int,
        message: str,
        from_: str | None = None,
        timestamp: int | datetime | None = None,
        encoding: str | None = None,
        dlr_url: str | None = None,
        flash: bool = False,
    ) -> SendResponse:
        """
        Send SMS to all contacts in a group.

        Args:
            to_group: Group ID to send to.
            message: SMS text (max 1530 characters).
            from_: Sender name.
            timestamp: Schedule send time.
            encoding: Character encoding.
            dlr_url: Webhook URL for delivery reports.
            flash: If True, send as flash SMS.

        Returns:
            SendResponse containing success and error details.
        """
        payload = self._build_send_group_payload(
            to_group=to_group,
            message=message,
            from_=from_,
            timestamp=timestamp,
            encoding=encoding,
            dlr_url=dlr_url,
            flash=flash,
        )
        response = await self._request("POST", "sendgroup", json=payload)
        return SendResponse.from_dict(response.json())

    async def get_credit(self) -> str:
        """
        Get remaining SMS credit balance.

        Returns:
            Credit balance as formatted string (e.g., "9.843,40").
        """
        response = await self._request("GET", "creditvalue")
        credit: str = response.json()["credit"]
        return credit

    async def delete_sms(self, reference: str) -> bool:
        """
        Delete/cancel a scheduled SMS by reference.

        The SMS must be scheduled at least 10 minutes in the future.

        Args:
            reference: The reference you set when sending the SMS.

        Returns:
            True if deleted successfully.
        """
        payload = {"reference": reference}
        await self._request("DELETE", "deletesms", json=payload)
        return True

    # ==================== Group Methods ====================

    async def create_group(self, group_name: str) -> Group:
        """
        Create a new contact group.

        Args:
            group_name: Display name for the group.

        Returns:
            The created Group object with its ID.
        """
        payload = {"groupName": group_name}
        response = await self._request("POST", "addgroup", json=payload)
        data = response.json()["success"]
        return Group.from_dict(data)

    async def list_groups(self) -> list[Group]:
        """
        List all contact groups.

        Returns:
            List of Group objects.
        """
        response = await self._request("GET", "listgroups")
        data = response.json()
        if isinstance(data, list):
            return [Group.from_dict(g) for g in data]
        return []

    async def update_group(self, group_id: int, group_name: str) -> bool:
        """
        Update a group's name.

        Args:
            group_id: ID of the group to update.
            group_name: New name for the group.

        Returns:
            True if updated successfully.
        """
        payload = {"groupId": group_id, "groupName": group_name}
        await self._request("PUT", "updategroup", json=payload)
        return True

    async def delete_group(self, group_id: int) -> bool:
        """
        Delete a group.

        The group must be empty (no contacts) to be deleted.

        Args:
            group_id: ID of the group to delete.

        Returns:
            True if deleted successfully.
        """
        payload = {"groupId": group_id}
        await self._request("DELETE", "deletegroup", json=payload)
        return True

    # ==================== Contact Methods ====================

    async def create_contact(
        self,
        group_id: int,
        phone_number: str,
        contact_name: str | None = None,
    ) -> bool:
        """
        Create a contact or add existing contact to a group.

        Args:
            group_id: ID of the group to add the contact to.
            phone_number: Phone number with country code.
            contact_name: Optional display name for the contact.

        Returns:
            True if created/added successfully.
        """
        payload: dict[str, Any] = {
            "groupId": group_id,
            "phoneNumber": phone_number,
        }
        if contact_name:
            payload["contactName"] = contact_name

        await self._request("POST", "addcontact", json=payload)
        return True

    async def list_contacts(self, group_id: int) -> list[Contact]:
        """
        List all contacts in a group.

        Args:
            group_id: ID of the group.

        Returns:
            List of Contact objects.
        """
        response = await self._request("GET", f"listcontacts/{group_id}")
        data = response.json()
        if isinstance(data, list):
            return [Contact.from_dict(c) for c in data]
        return []

    async def update_contact(
        self,
        group_id: int,
        phone_number: str,
        contact_name: str,
    ) -> bool:
        """
        Update a contact's name.

        Args:
            group_id: ID of the group containing the contact.
            phone_number: Phone number of the contact to update.
            contact_name: New name for the contact.

        Returns:
            True if updated successfully.
        """
        payload = {
            "groupId": group_id,
            "phoneNumber": phone_number,
            "contactName": contact_name,
        }
        await self._request("PUT", "updatecontact", json=payload)
        return True

    async def delete_contact(self, group_id: int, phone_number: str) -> bool:
        """
        Remove a contact from a group.

        Args:
            group_id: ID of the group to remove the contact from.
            phone_number: Phone number of the contact to remove.

        Returns:
            True if deleted/removed successfully.
        """
        payload = {
            "groupId": group_id,
            "phoneNumber": phone_number,
        }
        await self._request("DELETE", "deletecontact", json=payload)
        return True

    async def list_group_membership(self, phone_number: str) -> list[Group]:
        """
        List all groups a contact belongs to.

        Args:
            phone_number: Phone number of the contact.

        Returns:
            List of Group objects the contact is a member of.
        """
        response = await self._request("GET", f"listgroupmembership/{phone_number}")
        data = response.json().get("success", [])

        if isinstance(data, dict):
            return [Group.from_dict(data)]
        elif isinstance(data, list):
            return [Group.from_dict(g) for g in data]
        return []

    # ==================== Log Methods ====================

    async def get_log(
        self,
        to: str | None = None,
        from_date: int | datetime | None = None,
        to_date: int | datetime | None = None,
    ) -> list[LogEntry]:
        """
        Get SMS log entries.

        Can look back a maximum of 3 months from current time.

        Args:
            to: Filter by recipient phone number.
            from_date: Start date for log entries.
            to_date: End date for log entries.

        Returns:
            List of LogEntry objects.
        """
        params: dict[str, Any] = {}

        if to:
            params["to"] = to

        if from_date:
            if isinstance(from_date, datetime):
                params["fromDate"] = int(from_date.timestamp())
            else:
                params["fromDate"] = from_date

        if to_date:
            if isinstance(to_date, datetime):
                params["toDate"] = int(to_date.timestamp())
            else:
                params["toDate"] = to_date

        response = await self._request("GET", "getlog", params=params if params else None)
        data = response.json()

        if isinstance(data, list):
            return [LogEntry.from_dict(entry) for entry in data]
        return []
