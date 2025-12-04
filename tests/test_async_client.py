"""Tests for the asynchronous CPSMS client."""

import pytest
import respx
from httpx import Response

from cpsms import AsyncCPSMSClient, SMSFormat


BASE_URL = "https://api.cpsms.dk/v2"


@pytest.fixture
async def async_client():
    """Create a test async client."""
    async with AsyncCPSMSClient(username="testuser", api_key="test-api-key") as c:
        yield c


class TestAsyncSendSMS:
    """Tests for async send_sms method."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_send_single_recipient(self, async_client):
        """Test sending SMS to a single recipient asynchronously."""
        respx.post(f"{BASE_URL}/send").mock(
            return_value=Response(
                200,
                json={
                    "success": [
                        {"to": "4512345678", "cost": 1, "smsAmount": 1}
                    ]
                },
            )
        )

        result = await async_client.send_sms(
            to="4512345678",
            message="Hello!",
            from_="TestApp"
        )

        assert len(result.success) == 1
        assert result.success[0].to == "4512345678"
        assert result.success[0].cost == 1

    @respx.mock
    @pytest.mark.asyncio
    async def test_send_multiple_recipients(self, async_client):
        """Test sending SMS to multiple recipients asynchronously."""
        respx.post(f"{BASE_URL}/send").mock(
            return_value=Response(
                200,
                json={
                    "success": [
                        {"to": "4512345678", "cost": 1, "smsAmount": 1},
                        {"to": "4587654321", "cost": 1.6, "smsAmount": 1},
                    ]
                },
            )
        )

        result = await async_client.send_sms(
            to=["4512345678", "4587654321"],
            message="Bulk message!",
            from_="TestApp"
        )

        assert len(result.success) == 2


class TestAsyncCredit:
    """Tests for async get_credit method."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_credit(self, async_client):
        """Test getting credit balance asynchronously."""
        respx.get(f"{BASE_URL}/creditvalue").mock(
            return_value=Response(200, json={"credit": "9.843,40"})
        )

        credit = await async_client.get_credit()
        assert credit == "9.843,40"


class TestAsyncGroups:
    """Tests for async group management methods."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_group(self, async_client):
        """Test creating a group asynchronously."""
        respx.post(f"{BASE_URL}/addgroup").mock(
            return_value=Response(
                200,
                json={
                    "success": {"groupId": "12345", "groupName": "Test Group"}
                },
            )
        )

        group = await async_client.create_group("Test Group")
        assert group.group_id == 12345
        assert group.group_name == "Test Group"

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_groups(self, async_client):
        """Test listing groups asynchronously."""
        respx.get(f"{BASE_URL}/listgroups").mock(
            return_value=Response(
                200,
                json=[
                    {"groupId": 1, "groupName": "Group 1"},
                    {"groupId": 2, "groupName": "Group 2"},
                ],
            )
        )

        groups = await async_client.list_groups()
        assert len(groups) == 2


class TestAsyncContacts:
    """Tests for async contact management methods."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_contact(self, async_client):
        """Test creating a contact asynchronously."""
        respx.post(f"{BASE_URL}/addcontact").mock(
            return_value=Response(
                200, json={"success": "Contact created/added in group"}
            )
        )

        result = await async_client.create_contact(
            group_id=12345,
            phone_number="4512345678",
            contact_name="John Doe"
        )
        assert result is True

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_contacts(self, async_client):
        """Test listing contacts asynchronously."""
        respx.get(f"{BASE_URL}/listcontacts/12345").mock(
            return_value=Response(
                200,
                json=[
                    {
                        "phoneNumber": "4512345678",
                        "contactName": "John",
                        "timeAdded": 1481150286
                    },
                ],
            )
        )

        contacts = await async_client.list_contacts(group_id=12345)
        assert len(contacts) == 1
        assert contacts[0].phone_number == "4512345678"


class TestAsyncLog:
    """Tests for async log methods."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_log(self, async_client):
        """Test getting SMS log asynchronously."""
        respx.get(f"{BASE_URL}/getlog").mock(
            return_value=Response(
                200,
                json=[
                    {
                        "to": "4512345678",
                        "from": "MyApp",
                        "smsAmount": 1,
                        "pointPrice": 1.0,
                        "userReference": None,
                        "dlrStatus": 1,
                        "dlrStatusText": "Received",
                        "timeSent": 1466041455,
                    }
                ],
            )
        )

        log = await async_client.get_log()
        assert len(log) == 1
        assert log[0].to == "4512345678"
