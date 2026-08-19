# Tuya Resilience Companion

A Home Assistant custom integration that adds an **optional, one-shot local fallback path** for selected compatible Tuya Wi-Fi devices while leaving the official Tuya integration, Xtend Tuya, Smart Life/Tuya app, and existing production entities untouched.

> Status: early MVP development. Do not use this repository for production relay control yet.

## Design contract

The normal production path remains authoritative:

```text
Home Assistant -> Official Tuya / Xtend Tuya -> Tuya Cloud -> Device
```

The companion adds only an explicitly configured escape path:

```text
Home Assistant -> Tuya Resilience Companion -> one-shot local Tuya session -> Device -> disconnect
```

The integration must not:

- replace, rename, disable, import, or take ownership of existing Tuya entities;
- monkey-patch official Tuya or Xtend Tuya;
- maintain persistent TCP connections, heartbeats, polling loops, or reconnect daemons;
- continuously scan the LAN;
- require static DHCP reservations;
- expose local keys or cloud credentials in logs, entities, actions, or diagnostics.

## MVP scope

Initial support is deliberately narrow: direct, mains-powered Tuya Wi-Fi switch/plug/power-strip devices only. The first physical validation target is **Table Power Strip**.

Not in the initial MVP: Tuya Zigbee/gateways, battery sensors, IR, BLE, covers, climate, lights, cameras, scene buttons, Home Assistant's own power socket, Main Router recovery socket, or automatic migration of existing Tuya devices.

## Connection rule

Every local operation must use a bounded one-shot session:

1. Resolve and identity-check the device IP.
2. Connect locally.
3. Negotiate the configured Tuya protocol/session.
4. Read or write only what is required.
5. Confirm the result when possible.
6. Close the connection in `finally` / context-manager cleanup.
7. Leave no heartbeat task and no open device socket.

## Repository layout

The repository follows the documentation, CI, security and licence separation used in `ArrowSK/ha-astronomy-observer`, adapted to a Home Assistant **custom integration** rather than an App:

```text
custom_components/tuya_resilience/   Home Assistant integration
  protocol/                           isolated local Tuya transport adapter
  translations/                      custom-integration translations
docs/                                 architecture, security and development notes
tests/                                unit and contract tests
.github/                              CI and contribution templates
```

## Protocol dependency

The MVP uses [TinyTuya](https://github.com/jasonacox/tinytuya) as a pinned runtime dependency rather than copying LocalTuya or reimplementing Tuya cryptography. TinyTuya is MIT-licensed and supports Tuya protocols 3.1, 3.3, 3.4 and 3.5. The integration will use its non-persistent mode only and explicitly close every client after an operation.

TinyTuya's monitor/persistent-socket features are intentionally **not** used.

## Development phases

1. Repository and protocol-layer contract, including one-shot/no-heartbeat tests.
2. Home Assistant config-entry runtime, device registry, actions and diagnostics.
3. Passive/on-demand IP discovery and identity validation.
4. Table Power Strip read-only validation.
5. Explicitly authorised relay test with WAN available, then WAN disconnected.

No production entity-ID handover is part of the MVP.

## Licence

Project code is licensed under the MIT License. Third-party components retain their own licences; see `THIRD_PARTY_LICENSES.md` as the repository is built out.
