# Third-party software

## TinyTuya

Tuya Resilience Companion uses TinyTuya as an external runtime dependency.
No TinyTuya source code is copied into this repository.

Upstream: https://github.com/jasonacox/tinytuya

Licence: MIT License

Copyright (c) 2024 Jason Cox

TinyTuya remains licensed by its upstream authors under the MIT License. The
full upstream licence is distributed with the installed Python package and is
available in the upstream repository.

The integration deliberately uses TinyTuya's non-persistent device mode only.
TinyTuya's monitor/persistent socket facilities are outside the architecture
of this project.
