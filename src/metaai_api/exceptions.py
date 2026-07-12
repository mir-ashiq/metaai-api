"""Exception hierarchy for metaai_api."""
from __future__ import annotations


class MetaAIError(Exception):
    """Base exception for all metaai_api errors."""


class AuthenticationError(MetaAIError):
    """Raised when authentication fails (invalid/expired cookies)."""


class RateLimitError(MetaAIError):
    """Raised when Meta AI rate-limits your account."""


class GenerationError(MetaAIError):
    """Raised when image/video generation fails."""
    def __init__(self, message: str, detail: str = ""):
        super().__init__(message)
        self.detail = detail


class TimeoutError(MetaAIError):
    """Raised when a request times out."""


class ConnectionError(MetaAIError):
    """Raised when the WebSocket connection fails."""


class BrowserNotInstalledError(MetaAIError):
    """Raised when browser automation is needed but agent-browser isn't installed."""


class InvalidResponseError(MetaAIError):
    """Raised when the server returns an unexpected response."""
