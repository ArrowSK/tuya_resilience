"""Protocol-layer exceptions."""

from __future__ import annotations


class TuyaLocalError(Exception):
    """Base error for one-shot local Tuya operations."""


class TuyaLocalUsageError(TuyaLocalError):
    """Raised when the one-shot client contract is violated."""


class TuyaLocalBusyError(TuyaLocalError):
    """Reserved for manager-level per-device concurrency control."""


class TuyaLocalOperationError(TuyaLocalError):
    """Raised when TinyTuya reports a local protocol/device error."""

    def __init__(self, message: str, *, code: str | None = None) -> None:
        """Initialize a sanitized operation error."""
        super().__init__(message)
        self.code = code
