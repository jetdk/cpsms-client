# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-12-04

### Added

- Initial release
- Synchronous client (`CPSMSClient`)
- Asynchronous client (`AsyncCPSMSClient`)
- Full SMS API support:
  - `send_sms()` - Send to one or multiple recipients
  - `send_to_group()` - Send to contact group
  - `delete_sms()` - Cancel scheduled SMS
  - `get_credit()` - Check account balance
- Full Group API support:
  - `create_group()`
  - `list_groups()`
  - `update_group()`
  - `delete_group()`
- Full Contact API support:
  - `create_contact()`
  - `list_contacts()`
  - `update_contact()`
  - `delete_contact()`
  - `list_group_membership()`
- SMS Log API:
  - `get_log()` with date filtering
- Typed dataclasses for all response objects
- Custom exceptions for error handling
- Context manager support for both clients
- Support for scheduled SMS with datetime objects
- Support for Unicode messages (SMSFormat.UNICODE)
- Support for flash SMS
- Delivery report webhook URL support
