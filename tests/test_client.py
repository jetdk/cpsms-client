"""Tests for the synchronous CPSMS client."""

import pytest
import respx
from httpx import Response

from cpsms import (
    CPSMSClient,
    SMSFormat,
    SendResponse,
    Group,
    Contact,
    LogEntry,
    CPSMSError,
    AuthenticationError,
    InsufficientCreditError,
    BadRequestError,
)


BASE_URL = "https://api.cpsms.dk/v2"


@pytest.fixture
def client():
    """Create a test client."""
    with CPSMSClient(username="testuser", api_key="test-api-key") as c:
        yield c


class TestSendSMS:
    """Tests for send_sms method."""

    @respx.mock
    def test_send_single_recipient(self, client):
        """Test sending SMS to a single recipient."""
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

        result = client.send_sms(
            to="4512345678",
            message="Hello!",
            from_="TestApp"
        )

        assert len(result.success) == 1
        assert result.success[0].to == "4512345678"
        assert result.success[0].cost == 1
        assert len(result.errors) == 0

    @respx.mock
    def test_send_multiple_recipients(self, client):
        """Test sending SMS to multiple recipients."""
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

        result = client.send_sms(
            to=["4512345678", "4587654321"],
            message="Bulk message!",
            from_="TestApp"
        )

        assert len(result.success) == 2
        assert result.success[1].cost == 1.6

    @respx.mock
    def test_send_with_errors(self, client):
        """Test handling partial send failures."""
        respx.post(f"{BASE_URL}/send").mock(
            return_value=Response(
                200,
                json={
                    "success": [
                        {"to": "4512345678", "cost": 1, "smsAmount": 1}
                    ],
                    "error": [
                        {
                            "code": 409,
                            "message": "Phone number length invalid",
                            "to": "123"
                        }
                    ]
                },
            )
        )

        result = client.send_sms(
            to=["4512345678", "123"],
            message="Test",
            from_="App"
        )

        assert len(result.success) == 1
        assert len(result.errors) == 1
        assert result.errors[0].code == 409
        assert result.errors[0].to == "123"

    @respx.mock
    def test_send_unicode(self, client):
        """Test sending Unicode SMS."""
        respx.post(f"{BASE_URL}/send").mock(
            return_value=Response(
                200,
                json={"success": [{"to": "4512345678", "cost": 1, "smsAmount": 1}]},
            )
        )

        result = client.send_sms(
            to="4512345678",
            message="你好 🎉",
            from_="App",
            format_=SMSFormat.UNICODE
        )

        assert len(result.success) == 1

    @respx.mock
    def test_insufficient_credit(self, client):
        """Test handling insufficient credit error."""
        respx.post(f"{BASE_URL}/send").mock(
            return_value=Response(
                402,
                json={"error": {"message": "Not enough credit"}},
            )
        )

        with pytest.raises(InsufficientCreditError) as exc_info:
            client.send_sms(to="4512345678", message="Test", from_="App")

        assert exc_info.value.code == 402

    @respx.mock
    def test_authentication_error(self, client):
        """Test handling authentication error."""
        respx.post(f"{BASE_URL}/send").mock(
            return_value=Response(
                401,
                json={"error": {"message": "Invalid credentials"}},
            )
        )

        with pytest.raises(AuthenticationError) as exc_info:
            client.send_sms(to="4512345678", message="Test", from_="App")

        assert exc_info.value.code == 401


class TestCredit:
    """Tests for get_credit method."""

    @respx.mock
    def test_get_credit(self, client):
        """Test getting credit balance."""
        respx.get(f"{BASE_URL}/creditvalue").mock(
            return_value=Response(200, json={"credit": "9.843,40"})
        )

        credit = client.get_credit()
        assert credit == "9.843,40"


class TestGroups:
    """Tests for group management methods."""

    @respx.mock
    def test_create_group(self, client):
        """Test creating a group."""
        respx.post(f"{BASE_URL}/addgroup").mock(
            return_value=Response(
                200,
                json={
                    "success": {"groupId": "12345", "groupName": "Test Group"}
                },
            )
        )

        group = client.create_group("Test Group")
        assert group.group_id == 12345
        assert group.group_name == "Test Group"

    @respx.mock
    def test_list_groups(self, client):
        """Test listing groups."""
        respx.get(f"{BASE_URL}/listgroups").mock(
            return_value=Response(
                200,
                json=[
                    {"groupId": 1, "groupName": "Group 1"},
                    {"groupId": 2, "groupName": "Group 2"},
                ],
            )
        )

        groups = client.list_groups()
        assert len(groups) == 2
        assert groups[0].group_name == "Group 1"

    @respx.mock
    def test_update_group(self, client):
        """Test updating a group."""
        respx.put(f"{BASE_URL}/updategroup").mock(
            return_value=Response(200, json={"success": "groupId 12345 Updated"})
        )

        result = client.update_group(group_id=12345, group_name="New Name")
        assert result is True

    @respx.mock
    def test_delete_group(self, client):
        """Test deleting a group."""
        respx.delete(f"{BASE_URL}/deletegroup").mock(
            return_value=Response(200, json={"success": "Group 12345 deleted"})
        )

        result = client.delete_group(group_id=12345)
        assert result is True


class TestContacts:
    """Tests for contact management methods."""

    @respx.mock
    def test_create_contact(self, client):
        """Test creating a contact."""
        respx.post(f"{BASE_URL}/addcontact").mock(
            return_value=Response(
                200, json={"success": "Contact created/added in group"}
            )
        )

        result = client.create_contact(
            group_id=12345,
            phone_number="4512345678",
            contact_name="John Doe"
        )
        assert result is True

    @respx.mock
    def test_list_contacts(self, client):
        """Test listing contacts."""
        respx.get(f"{BASE_URL}/listcontacts/12345").mock(
            return_value=Response(
                200,
                json=[
                    {
                        "phoneNumber": "4512345678",
                        "contactName": "John",
                        "timeAdded": 1481150286
                    },
                    {
                        "phoneNumber": "4587654321",
                        "contactName": "Jane",
                        "timeAdded": 1481150300
                    },
                ],
            )
        )

        contacts = client.list_contacts(group_id=12345)
        assert len(contacts) == 2
        assert contacts[0].phone_number == "4512345678"
        assert contacts[0].contact_name == "John"
        assert contacts[0].time_added is not None


class TestLog:
    """Tests for log methods."""

    @respx.mock
    def test_get_log(self, client):
        """Test getting SMS log."""
        respx.get(f"{BASE_URL}/getlog").mock(
            return_value=Response(
                200,
                json=[
                    {
                        "to": "4512345678",
                        "from": "MyApp",
                        "smsAmount": 1,
                        "pointPrice": 1.0,
                        "userReference": "ref-123",
                        "dlrStatus": 1,
                        "dlrStatusText": "Received",
                        "timeSent": 1466041455,
                    }
                ],
            )
        )

        log = client.get_log()
        assert len(log) == 1
        assert log[0].to == "4512345678"
        assert log[0].from_ == "MyApp"
        assert log[0].dlr_status == 1


class TestModels:
    """Tests for data models."""

    def test_send_response_from_dict(self):
        """Test SendResponse.from_dict parsing."""
        data = {
            "success": [{"to": "4512345678", "cost": 1, "smsAmount": 2}],
            "error": [{"code": 400, "message": "Invalid", "to": "123"}],
        }

        response = SendResponse.from_dict(data)
        assert len(response.success) == 1
        assert response.success[0].sms_amount == 2
        assert len(response.errors) == 1
        assert response.errors[0].code == 400

    def test_send_response_single_success(self):
        """Test SendResponse with single success dict (not list)."""
        data = {"success": {"to": "4512345678", "cost": 1}}

        response = SendResponse.from_dict(data)
        assert len(response.success) == 1

    def test_group_from_dict(self):
        """Test Group.from_dict parsing."""
        data = {"groupId": "12345", "groupName": "Test"}

        group = Group.from_dict(data)
        assert group.group_id == 12345
        assert group.group_name == "Test"

    def test_contact_from_dict(self):
        """Test Contact.from_dict parsing."""
        data = {
            "phoneNumber": "4512345678",
            "contactName": "John",
            "timeAdded": 1481150286,
        }

        contact = Contact.from_dict(data)
        assert contact.phone_number == "4512345678"
        assert contact.contact_name == "John"
        assert contact.time_added is not None

    def test_log_entry_from_dict(self):
        """Test LogEntry.from_dict parsing."""
        data = {
            "to": "4512345678",
            "from": "App",
            "smsAmount": 1,
            "pointPrice": 1.0,
            "userReference": None,
            "dlrStatus": 1,
            "dlrStatusText": "Received",
            "timeSent": 1466041455,
        }

        entry = LogEntry.from_dict(data)
        assert entry.to == "4512345678"
        assert entry.from_ == "App"
        assert entry.time_sent is not None
