# Development

## Phase 1: protocol safety foundation

The first milestone is intentionally not a usable relay controller. It proves
the most important negative requirement first: a local command must not leave a
persistent Tuya connection or heartbeat behind.

Install test dependencies and run:

```sh
python -m pip install -e ".[test]"
pytest
ruff check .
```

The protocol tests use fake devices. They do not contact the LAN and never use
real Tuya credentials.

## Phase 2: Home Assistant lifecycle

Add ConfigEntry/config flow, per-entry runtime manager, options, device
registry, actions/services and diagnostics. No physical relay operation is
required for this phase.

## Phase 3: discovery and identity

Add passive UDP discovery plus an explicit bounded rediscovery action. Validate
Device ID before accepting a changed IP. Do not implement forced subnet-wide
TCP scanning.

## Phase 4: first physical validation

Use Table Power Strip only:

1. Configure without changing any existing Tuya/Xtend entity.
2. Run local status query only.
3. Confirm the socket closes.
4. Repeat read-only queries.
5. Confirm normal cloud/Xtend operation remains unaffected.
6. Only then perform one explicitly authorised relay command.
7. Repeat one authorised command with WAN disconnected.
8. Restore WAN and verify official Tuya/Xtend operation.

Stop if unrelated Tuya devices become unreliable, cloud availability changes,
repeated reconnects appear or Smart Life control degrades.
