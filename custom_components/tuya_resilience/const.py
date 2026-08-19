"""Constants for Tuya Resilience Companion."""

from __future__ import annotations

DOMAIN = "tuya_resilience"
INTEGRATION_VERSION = "0.1.0"

CONF_DEVICE_ID = "device_id"
CONF_LOCAL_KEY = "local_key"
CONF_PROTOCOL_VERSION = "protocol_version"
CONF_LAST_KNOWN_IP = "last_known_ip"
CONF_CLOUD_ENTITY_ID = "cloud_entity_id"
CONF_FALLBACK_ENABLED = "fallback_enabled"
CONF_FALLBACK_MODE = "fallback_mode"

PROTOCOL_AUTO = "auto"
SUPPORTED_PROTOCOLS = ("3.1", "3.3", "3.4", "3.5")

FALLBACK_DISABLED = "disabled"
FALLBACK_MANUAL_ONLY = "manual_only"
FALLBACK_CLOUD_UNAVAILABLE = "cloud_unavailable"
