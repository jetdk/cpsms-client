"""Custom exceptions for the CPSMS API client."""

from __future__ import annotations


class CPSMSError(Exception):
    """Base exception for CPSMS API errors."""

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"CPSMS Error {code}: {message}")


class AuthenticationError(CPSMSError):
    """Authentication failed (HTTP 401).
    
    This usually means invalid username or API key.
    """
    pass


class InsufficientCreditError(CPSMSError):
    """Not enough SMS credits (HTTP 402).
    
    Top up your account at cpsms.dk to continue sending.
    """
    pass


class ForbiddenError(CPSMSError):
    """IP validation failed (HTTP 403).
    
    Your IP address may not be whitelisted.
    """
    pass


class NotFoundError(CPSMSError):
    """Resource not found (HTTP 404).
    
    The requested endpoint or resource does not exist.
    """
    pass


class ConflictError(CPSMSError):
    """Nothing to return based on posted data (HTTP 409).
    
    The requested operation could not be completed with the given data.
    """
    pass


class BadRequestError(CPSMSError):
    """Invalid request (HTTP 400).
    
    There is something wrong with the request parameters.
    """
    pass
