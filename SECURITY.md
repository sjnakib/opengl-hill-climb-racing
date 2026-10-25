# Security Policy

## Supported versions

| Version | Supported |
| --- | --- |
| 0.1.x | Yes, the current `main` and releases from v0.1.1 on |

## Reporting a vulnerability

Use GitHub private vulnerability reporting: repo, then Security, then Report
a vulnerability. Please do not open public issues for security reports.

The attack surface here is intentionally small. The game is offline-only, it
does not network (SPECS §2), it reads and writes only its own config and
save files under the paths in SPECS §9, and it ships self-contained
binaries. In scope: crafted config or save files (parser safety), path
handling, asset parsing, and bundle integrity. Out of scope: anything that
would need the game to talk to the internet. It cannot, by design.
