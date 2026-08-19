# Security policy

## Secrets

Tuya local keys, cloud client secrets, access tokens, refresh tokens and
derived session keys are secrets.

They must not appear in:

- normal or debug logs;
- entity states or attributes;
- Home Assistant action/service fields;
- diagnostics downloads;
- issue reports or screenshots;
- test fixtures committed to this repository.

Use synthetic values in tests.

## Local-network trust boundary

An IP address is not a device identity. A host answering on TCP port 6668 must
never be trusted solely because the port is open. Before a write, the runtime
must have validated that the LAN discovery identity maps the configured Tuya
Device ID to the candidate IP. An identity mismatch is a hard stop.

## Reporting

For a security-sensitive issue, avoid posting real device IDs, local keys,
cloud credentials or private LAN details in a public issue. Provide a minimal
redacted reproduction instead.
