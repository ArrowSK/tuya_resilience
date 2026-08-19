# Architecture

Tuya Resilience Companion is deliberately not another Tuya state authority.
Official Tuya/Xtend Tuya remains the normal Home Assistant path. This
integration exists only to provide an explicitly configured local escape path.

## Runtime shape

```text
                    Home Assistant
                         |
          +--------------+---------------+
          |                              |
          v                              v
 Official Tuya / Xtend           Tuya Resilience
          |                              |
          v                              v
      Tuya Cloud              per-device operation lock
          |                              |
          v                              v
        Device                  identity/IP resolver
                                         |
                                         v
                                one-shot protocol client
                                         |
                         TCP connect -> command -> close
```

No component in the local path owns a permanent TCP session to a device.

## Layers

`protocol/` is independent from Home Assistant lifecycle and entity code. It
wraps a proven Tuya protocol implementation behind a narrow asynchronous API.

The Home Assistant layer will later provide:

- ConfigEntry lifecycle and `runtime_data`;
- per-device manager, lock, rate limit and backoff;
- device registry entry;
- explicit actions/services;
- diagnostic entities;
- options flow;
- passive/on-demand LAN discovery.

A DataUpdateCoordinator is intentionally not part of the design because the
MVP must not periodically poll devices.

## One-shot operation invariant

A `TuyaLocalClient` instance represents exactly one local operation. It requires
an already resolved IP address; it does not scan the LAN itself.

```python
async with TuyaLocalClient(...) as client:
    status = await client.status()
```

or:

```python
async with TuyaLocalClient(...) as client:
    result = await client.set_dp(1, True)
```

The protocol adapter configures TinyTuya with `persist=False`, a bounded socket
retry count and an explicit timeout. The context manager calls `close()` in all
exit paths. A second operation on the same client instance is rejected so a
caller cannot accidentally turn a one-shot object into a session.

Verification of a write, when enabled later, will be a separate bounded
one-shot read rather than keeping the write socket alive.

## IP and identity boundary

IP resolution is outside the protocol adapter.

Candidate IP priority will be:

1. passive Tuya LAN discovery;
2. previously identity-validated last-known IP;
3. targeted, temporary Tuya discovery.

A manually supplied IP starts as unverified. An IP is not accepted merely
because TCP port 6668 responds.

Before a local write, the manager must have evidence that Tuya LAN discovery
reported the configured Device ID at that IP. If discovery reports another
Device ID, the connection is closed and the candidate IP is not cached.

No permanent subnet scanner is permitted.

## Failure isolation

Each configured device will have its own manager, lock and backoff state.
Failures are local to that manager.

Startup never waits for a Tuya device to answer. An offline device does not
prevent the integration or another configured device from loading.

Automatic retry remains bounded. Repeated failures move the affected device
into backoff rather than creating a reconnect loop.

## State ownership

The MVP does not create replacement switch entities. Existing official
Tuya/Xtend entities keep their current IDs and remain authoritative.

The companion will expose only diagnostics/configuration entities and explicit
local actions until wrapper entities are deliberately designed in a future
version.

## Security

Local keys are stored only in Home Assistant config-entry data and passed to
the protocol adapter in memory. They are never emitted into diagnostics,
entity attributes or service/action schemas.

Diagnostics will use Home Assistant redaction helpers and maintain an explicit
denylist for all current and future credential fields.
