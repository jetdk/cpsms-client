# CPSMS-client

[![PyPI version](https://badge.fury.io/py/cpsms.svg)](https://badge.fury.io/py/cpsms-client)
[![Python Versions](https://img.shields.io/pypi/pyversions/cpsms.svg)](https://pypi.org/project/cpsms-client/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python client for the [CPSMS.dk](https://cpsms.dk) SMS Gateway API with both synchronous and asynchronous support.

## Features

- ✅ Full API coverage (SMS, Groups, Contacts, Logs)
- ✅ Both sync and async clients
- ✅ Type hints throughout
- ✅ Dataclasses for all response objects
- ✅ Custom exceptions for error handling
- ✅ Context manager support

## Installation

```bash
pip install cpsms-client
```

## Quick Start

### Synchronous Usage

```python
from cpsms import CPSMSClient

with CPSMSClient(username="your_username", api_key="your_api_key") as client:
    # Send an SMS
    result = client.send_sms(
        to="4512345678",
        message="Hello from Python!",
        from_="MyApp"
    )
    print(f"Sent! Cost: {result.success[0].cost} points")

    # Check your credit balance
    credit = client.get_credit()
    print(f"Remaining credit: {credit}")
```

### Asynchronous Usage

```python
import asyncio
from cpsms import AsyncCPSMSClient

async def main():
    async with AsyncCPSMSClient(username="your_username", api_key="your_api_key") as client:
        result = await client.send_sms(
            to="4512345678",
            message="Hello from async Python!",
            from_="MyApp"
        )
        print(f"Sent! Cost: {result.success[0].cost} points")

asyncio.run(main())
```

## Getting Your API Credentials

1. Create an account at [cpsms.dk](https://www.cpsms.dk/demologin.php) (you get 10 free SMS points)
2. Log in to your dashboard at [cpsms.dk/login](https://cpsms.dk/login)
3. Navigate to **INDSTILLINGER → API**
4. Generate your API key

## API Reference

### Sending SMS

```python
from cpsms import CPSMSClient, SMSFormat
from datetime import datetime, timedelta

with CPSMSClient(username="user", api_key="key") as client:
    # Simple send
    result = client.send_sms(
        to="4512345678",
        message="Hello!",
        from_="MyApp"
    )

    # Send to multiple recipients
    result = client.send_sms(
        to=["4512345678", "4587654321"],
        message="Bulk message!",
        from_="MyApp"
    )

    # Schedule for later
    result = client.send_sms(
        to="4512345678",
        message="This arrives in 1 hour",
        from_="MyApp",
        timestamp=datetime.now() + timedelta(hours=1),
        reference="my-ref-123"  # Required if you want to cancel later
    )

    # Send with delivery report webhook
    result = client.send_sms(
        to="4512345678",
        message="Track me!",
        from_="MyApp",
        dlr_url="https://myserver.com/webhook"
    )

    # Send Unicode (for emojis, Chinese characters, etc.)
    result = client.send_sms(
        to="4512345678",
        message="你好 🎉",
        from_="MyApp",
        format_=SMSFormat.UNICODE
    )

    # Send flash SMS (appears directly on screen)
    result = client.send_sms(
        to="4512345678",
        message="URGENT!",
        from_="MyApp",
        flash=True
    )
```

### Managing Groups

```python
with CPSMSClient(username="user", api_key="key") as client:
    # Create a group
    group = client.create_group("VIP Customers")
    print(f"Created group ID: {group.group_id}")

    # List all groups
    groups = client.list_groups()
    for g in groups:
        print(f"{g.group_name} (ID: {g.group_id})")

    # Update group name
    client.update_group(group_id=12345, group_name="Premium Customers")

    # Delete group (must be empty)
    client.delete_group(group_id=12345)

    # Send SMS to entire group
    result = client.send_to_group(
        to_group=12345,
        message="Hello VIP customers!",
        from_="MyStore"
    )
```

### Managing Contacts

```python
with CPSMSClient(username="user", api_key="key") as client:
    # Add contact to a group
    client.create_contact(
        group_id=12345,
        phone_number="4512345678",
        contact_name="John Doe"
    )

    # List contacts in a group
    contacts = client.list_contacts(group_id=12345)
    for contact in contacts:
        print(f"{contact.contact_name}: {contact.phone_number}")

    # Update contact name
    client.update_contact(
        group_id=12345,
        phone_number="4512345678",
        contact_name="John Smith"
    )

    # Find which groups a contact belongs to
    groups = client.list_group_membership("4512345678")
    print(f"Contact is in {len(groups)} groups")

    # Remove contact from group
    client.delete_contact(group_id=12345, phone_number="4512345678")
```

### Viewing Logs

```python
from datetime import datetime, timedelta

with CPSMSClient(username="user", api_key="key") as client:
    # Get recent log entries (up to 3 months back)
    log = client.get_log()
    for entry in log:
        print(f"{entry.time_sent}: To {entry.to} - Status: {entry.dlr_status_text}")

    # Filter by recipient
    log = client.get_log(to="4512345678")

    # Filter by date range
    log = client.get_log(
        from_date=datetime.now() - timedelta(days=7),
        to_date=datetime.now()
    )
```

### Account Management

```python
with CPSMSClient(username="user", api_key="key") as client:
    # Check credit balance
    credit = client.get_credit()
    print(f"Balance: {credit}")

    # Cancel a scheduled SMS (must be >10 min before send time)
    client.delete_sms(reference="my-ref-123")
```

## Error Handling

```python
from cpsms import (
    CPSMSClient,
    CPSMSError,
    AuthenticationError,
    InsufficientCreditError,
    BadRequestError,
)

with CPSMSClient(username="user", api_key="key") as client:
    try:
        result = client.send_sms(to="4512345678", message="Hello!", from_="App")
    except AuthenticationError:
        print("Invalid username or API key")
    except InsufficientCreditError:
        print("Not enough SMS credits - please top up!")
    except BadRequestError as e:
        print(f"Invalid request: {e.message}")
    except CPSMSError as e:
        print(f"API error {e.code}: {e.message}")
```

### Exception Types

| Exception | HTTP Code | Description |
|-----------|-----------|-------------|
| `AuthenticationError` | 401 | Invalid credentials |
| `InsufficientCreditError` | 402 | Not enough SMS credits |
| `ForbiddenError` | 403 | IP not whitelisted |
| `NotFoundError` | 404 | Resource not found |
| `ConflictError` | 409 | Operation conflict |
| `BadRequestError` | 400 | Invalid parameters |
| `CPSMSError` | * | Base exception for all API errors |

## Async Concurrent Requests

```python
import asyncio
from cpsms import AsyncCPSMSClient

async def send_bulk():
    async with AsyncCPSMSClient(username="user", api_key="key") as client:
        # Send to multiple recipients concurrently
        tasks = [
            client.send_sms(to=num, message="Hello!", from_="MyApp")
            for num in ["4512345678", "4587654321", "4599887766"]
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                print(f"Error: {result}")
            else:
                for sms in result.success:
                    print(f"Sent to {sms.to}")

asyncio.run(send_bulk())
```

## Response Objects

### SendResponse

```python
result = client.send_sms(to=["4512345678", "invalid"], message="Hi", from_="App")

# Successful sends
for sms in result.success:
    print(f"To: {sms.to}, Cost: {sms.cost}, Segments: {sms.sms_amount}")

# Failed sends
for error in result.errors:
    print(f"To: {error.to}, Error: {error.message} (code: {error.code})")
```

### Group

```python
group = client.create_group("My Group")
print(f"ID: {group.group_id}, Name: {group.group_name}")
```

### Contact

```python
contacts = client.list_contacts(group_id=12345)
for c in contacts:
    print(f"Name: {c.contact_name}")
    print(f"Phone: {c.phone_number}")
    print(f"Added: {c.time_added}")  # datetime object
```

### LogEntry

```python
log = client.get_log()
for entry in log:
    print(f"To: {entry.to}")
    print(f"From: {entry.from_}")
    print(f"Segments: {entry.sms_amount}")
    print(f"Cost: {entry.point_price}")
    print(f"Reference: {entry.user_reference}")
    print(f"Status: {entry.dlr_status} - {entry.dlr_status_text}")
    print(f"Sent: {entry.time_sent}")  # datetime object
```

## SMS Limits

| Format | Single SMS | Multipart (per segment) |
|--------|------------|-------------------------|
| GSM | 160 chars | 153 chars |
| Unicode | 70 chars | 67 chars |

Maximum message length: **1530 characters** (10 SMS segments joined)

## Development

```bash
# Clone the repository
git clone https://github.com/jetdk/cpsms-client.git
<<<<<<< HEAD
cd cpsms-client
=======
cd cpsms
>>>>>>> 8cc22b3acf8430a6d0279ed57bee173b41907922

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run type checking
mypy src/cpsms

# Run linting
ruff check src/cpsms-client
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Links

- [CPSMS.dk](https://cpsms.dk) - Official website
- [API Documentation](https://api.cpsms.dk/documentation/index.html) - Official API docs
- [PyPI Package](https://pypi.org/project/cpsms-client/) - Python Package Index
