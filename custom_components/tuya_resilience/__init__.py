"""Tuya Resilience Companion.

The initial package intentionally registers no device-control actions. The
protocol layer is developed and tested first; Home Assistant config-entry
runtime is added in the next milestone.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the integration package."""
    return True
