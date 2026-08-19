"""One-shot local Tuya protocol client.

This module deliberately knows nothing about Home Assistant entities, config
entries, discovery or fallback policy. It receives an already resolved IP and
performs exactly one bounded local operation.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from ipaddress import ip_address
from typing import Any, Protocol

import tinytuya

from .errors import TuyaLocalOperationError, TuyaLocalUsageError

DEFAULT_CONNECTION_TIMEOUT = 3.0
DEFAULT_RETRY_LIMIT = 1
DEFAULT_RETRY_DELAY = 0.25


class _TinyTuyaDevice(Protocol):
    """Narrow interface used by the adapter and fake devices in tests."""

    socket: Any
    socketPersistent: bool

    def status(self, nowait: bool = False) -> Any:
        """Return device status."""

    def set_value(self, index: int, value: Any, nowait: bool = False) -> Any:
        """Set one DP."""

    def close(self) -> None:
        """Close any remaining socket."""


DeviceFactory = Callable[..., _TinyTuyaDevice]


class TuyaLocalClient:
    """Execute exactly one local Tuya operation and then become unusable."""

    def __init__(
        self,
        *,
        device_id: str,
        local_key: str,
        address: str,
        protocol_version: str,
        connection_timeout: float = DEFAULT_CONNECTION_TIMEOUT,
        retry_limit: int = DEFAULT_RETRY_LIMIT,
        retry_delay: float = DEFAULT_RETRY_DELAY,
        device_factory: DeviceFactory | None = None,
    ) -> None:
        """Create a one-shot client without opening a TCP connection."""
        if not device_id:
            raise ValueError("device_id is required")
        if not local_key:
            raise ValueError("local_key is required")
        if protocol_version not in {"3.1", "3.3", "3.4", "3.5"}:
            raise ValueError("protocol_version must be one of 3.1, 3.3, 3.4 or 3.5")
        if retry_limit < 1:
            raise ValueError("retry_limit must be at least 1")
        if connection_timeout <= 0:
            raise ValueError("connection_timeout must be positive")
        if retry_delay < 0:
            raise ValueError("retry_delay cannot be negative")

        parsed_address = ip_address(address)
        if parsed_address.is_unspecified:
            raise ValueError("address must be a resolved device IP")

        self._device_id = device_id
        self._local_key = local_key
        self._address = str(parsed_address)
        self._protocol_version = protocol_version
        self._connection_timeout = connection_timeout
        self._retry_limit = retry_limit
        self._retry_delay = retry_delay
        self._device_factory = device_factory or tinytuya.Device

        self._device: _TinyTuyaDevice | None = None
        self._entered = False
        self._operation_used = False
        self._closed = False

    async def __aenter__(self) -> "TuyaLocalClient":
        """Build the non-persistent TinyTuya device object."""
        if self._entered:
            raise TuyaLocalUsageError("client context cannot be entered twice")

        self._entered = True
        self._device = self._device_factory(
            self._device_id,
            address=self._address,
            local_key=self._local_key,
            version=float(self._protocol_version),
            persist=False,
            connection_timeout=self._connection_timeout,
            connection_retry_limit=self._retry_limit,
            connection_retry_delay=self._retry_delay,
        )

        if getattr(self._device, "socketPersistent", False):
            await self.aclose()
            raise TuyaLocalUsageError("protocol backend unexpectedly enabled persistence")

        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        """Always close the backend, including exceptional exits."""
        await self.aclose()

    async def status(self) -> dict[str, Any]:
        """Read status in the client's single permitted operation."""
        result = await self._run_once(self._status_sync)
        if not isinstance(result, dict):
            raise TuyaLocalOperationError("local status returned an unexpected response")
        return result

    async def set_dp(self, dp: int, value: Any) -> dict[str, Any]:
        """Set one DP and wait for the protocol response."""
        if not isinstance(dp, int) or dp <= 0:
            raise ValueError("dp must be a positive integer")

        result = await self._run_once(lambda: self._set_dp_sync(dp, value))
        if not isinstance(result, dict):
            raise TuyaLocalOperationError("local DP write returned an unexpected response")
        return result

    async def aclose(self) -> None:
        """Close the TinyTuya backend and release the reference."""
        if self._closed:
            return

        self._closed = True
        device, self._device = self._device, None
        if device is not None:
            await asyncio.to_thread(device.close)

    async def _run_once(self, operation: Callable[[], Any]) -> Any:
        """Run one blocking TinyTuya call in a worker thread."""
        if not self._entered or self._device is None:
            raise TuyaLocalUsageError("client must be used inside 'async with'")
        if self._closed:
            raise TuyaLocalUsageError("client is already closed")
        if self._operation_used:
            raise TuyaLocalUsageError("one-shot client already performed an operation")

        self._operation_used = True
        result = await asyncio.to_thread(operation)
        self._raise_for_error_result(result)
        return result

    def _status_sync(self) -> Any:
        """Blocking status call, executed in a worker thread."""
        assert self._device is not None
        return self._device.status(nowait=False)

    def _set_dp_sync(self, dp: int, value: Any) -> Any:
        """Blocking DP write, executed in a worker thread."""
        assert self._device is not None
        return self._device.set_value(dp, value, nowait=False)

    @staticmethod
    def _raise_for_error_result(result: Any) -> None:
        """Turn TinyTuya error dictionaries into sanitized typed exceptions."""
        if not isinstance(result, dict):
            return

        code = result.get("Err")
        if code is None:
            code = result.get("Error")

        if code is not None:
            raise TuyaLocalOperationError(
                "local Tuya operation failed",
                code=str(code),
            )
