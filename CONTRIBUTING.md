# Contributing

Tuya Resilience Companion is intentionally conservative because it can control
mains-powered devices.

Before changing behavior, preserve these invariants:

1. Official Tuya and Xtend Tuya remain authoritative and untouched.
2. Local TCP sessions are one-shot and non-persistent.
3. No heartbeat, permanent listener client, periodic device polling, reconnect
   daemon, or subnet-wide background scan may be introduced.
4. Device identity must be verified before a local write.
5. Local keys, session keys and cloud credentials must never be logged or exposed.
6. One device failure must not trigger work against other devices.

Run the test suite before opening a pull request:

```sh
python -m pip install \
  "tinytuya==1.20.0" \
  "pytest>=8.4,<9" \
  "pytest-asyncio>=1.1,<2" \
  "ruff>=0.12,<1"
pytest
ruff check .
```

Physical testing is separate from unit testing and must start read-only. Do not
perform relay operations unless the test step explicitly authorises them.
