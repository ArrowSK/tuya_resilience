"""Tests for the one-shot local protocol contract."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from custom_components.tuya_resilience.protocol.client import TuyaLocalClient
from custom_components.tuya_resilience.protocol.errors import (
    TuyaLocalOperationError,
    TuyaLocalUsageError,
)


class FakeDevice:
    """TinyTuya-shaped fake that never touches the network."""

    def __init__(
        self,
        device_id: str,
        *,
        address: str,
        local_key: str,
        version: float,
        persist: bool,
        connection_timeout: float,
        connection_retry_limit: int,
        connection_retry_delay: float,
        status_result: Any = None,
        set_result: Any = None,
        raise_status: Exception | None = None,
        raise_set: Exception | None = None,
    ) -> None:
        self.device_id = device_id
        self.address = address
        self.local_key = local_key
        self.version = version
        self.socketPersistent = persist
        self.connection_timeout = connection_timeout
        self.connection_retry_limit = connection_retry_limit
        self.connection_retry_delay = connection_retry_delay
        self.status_result = status_result if status_result is not None else {"dps": {"1": True}}
        self.set_result = set_result if set_result is not None else {"dps": {"1": True}}
        self.raise_status = raise_status
        self.raise_set = raise_set
        self.socket = object()
        self.close_calls = 0
        self.status_calls = 0
        self.set_calls = 0

    def status(self, nowait: bool = False) -> Any:
        self.status_calls += 1
        if self.raise_status is not None:
            raise self.raise_status
        return self.status_result

    def set_value(self, index: int, value: Any, nowait: bool = False) -> Any:
        self.set_calls += 1
        if self.raise_set is not None:
            raise self.raise_set
        return self.set_result

    def close(self) -> None:
        self.close_calls += 1
        self.socket = None


class Factory:
    """Capture construction arguments and expose the latest fake."""

    def __init__(self, **fake_overrides: Any) -> None:
        self.fake_overrides = fake_overrides
        self.calls: list[dict[str, Any]] = []
        self.device: FakeDevice | None = None

    def __call__(self, device_id: str, **kwargs: Any) -> FakeDevice:
        self.calls.append({"device_id": device_id, **kwargs})
        self.device = FakeDevice(device_id, **kwargs, **self.fake_overrides)
        return self.device


def make_client(factory: Factory) -> TuyaLocalClient:
    return TuyaLocalClient(
        device_id="test-device-id",
        local_key="0123456789abcdef",
        address="192.0.2.10",
        protocol_version="3.4",
        device_factory=factory,
    )


@pytest.mark.asyncio
async def test_status_success_closes_connection() -> None:
    factory = Factory(status_result={"dps": {"1": True, "18": 123}})
    client = make_client(factory)

    async with client:
        result = await client.status()

    assert result == {"dps": {"1": True, "18": 123}}
    assert factory.device is not None
    assert factory.device.status_calls == 1
    assert factory.device.close_calls == 1
    assert factory.device.socket is None


@pytest.mark.asyncio
async def test_dp_write_success_closes_connection() -> None:
    factory = Factory(set_result={"dps": {"1": False}})
    client = make_client(factory)

    async with client:
        result = await client.set_dp(1, False)

    assert result == {"dps": {"1": False}}
    assert factory.device is not None
    assert factory.device.set_calls == 1
    assert factory.device.close_calls == 1
    assert factory.device.socket is None


@pytest.mark.asyncio
async def test_failure_still_closes_connection() -> None:
    factory = Factory(raise_status=TimeoutError("synthetic timeout"))
    client = make_client(factory)

    with pytest.raises(TimeoutError, match="synthetic timeout"):
        async with client:
            await client.status()

    assert factory.device is not None
    assert factory.device.close_calls == 1
    assert factory.device.socket is None


@pytest.mark.asyncio
async def test_tinytuya_error_is_sanitized_and_connection_closes() -> None:
    factory = Factory(status_result={"Err": "905", "Error": "do not echo backend details"})
    client = make_client(factory)

    with pytest.raises(TuyaLocalOperationError, match="local Tuya operation failed") as caught:
        async with client:
            await client.status()

    assert caught.value.code == "905"
    assert "do not echo" not in str(caught.value)
    assert factory.device is not None
    assert factory.device.close_calls == 1


@pytest.mark.asyncio
async def test_backend_is_constructed_non_persistent_with_bounded_retry() -> None:
    factory = Factory()
    client = make_client(factory)

    async with client:
        await client.status()

    assert len(factory.calls) == 1
    args = factory.calls[0]
    assert args["persist"] is False
    assert args["connection_retry_limit"] == 1
    assert args["connection_retry_delay"] == 0.25
    assert args["connection_timeout"] == 3.0


@pytest.mark.asyncio
async def test_second_operation_same_context_is_rejected() -> None:
    factory = Factory()
    client = make_client(factory)

    async with client:
        await client.status()
        with pytest.raises(TuyaLocalUsageError, match="already performed"):
            await client.set_dp(1, True)

    assert factory.device is not None
    assert factory.device.status_calls == 1
    assert factory.device.set_calls == 0
    assert factory.device.close_calls == 1


@pytest.mark.asyncio
async def test_client_does_not_create_background_heartbeat_task() -> None:
    factory = Factory()
    client = make_client(factory)
    current = asyncio.current_task()
    before = {task for task in asyncio.all_tasks() if task is not current}

    async with client:
        await client.status()

    await asyncio.sleep(0)
    after = {task for task in asyncio.all_tasks() if task is not current}

    assert after == before
    assert factory.device is not None
    assert factory.device.socketPersistent is False
    assert factory.device.socket is None


@pytest.mark.asyncio
async def test_context_without_operation_still_closes_backend() -> None:
    factory = Factory()
    client = make_client(factory)

    async with client:
        pass

    assert factory.device is not None
    assert factory.device.close_calls == 1
    assert factory.device.socket is None


@pytest.mark.parametrize("address", ["0.0.0.0", "::"])
def test_unspecified_address_is_rejected(address: str) -> None:
    with pytest.raises(ValueError, match="resolved device IP"):
        TuyaLocalClient(
            device_id="test-device-id",
            local_key="0123456789abcdef",
            address=address,
            protocol_version="3.4",
            device_factory=Factory(),
        )


def test_auto_protocol_is_not_accepted_by_low_level_client() -> None:
    with pytest.raises(ValueError, match="protocol_version"):
        TuyaLocalClient(
            device_id="test-device-id",
            local_key="0123456789abcdef",
            address="192.0.2.10",
            protocol_version="auto",
            device_factory=Factory(),
        )
