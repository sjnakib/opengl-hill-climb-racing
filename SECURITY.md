# Security Policy

## Supported versions

| Version | Supported |
| --- | --- |
| 0.1.x | yes (current `main` and releases ≥ v0.1.1) |

## Reporting a vulnerability

Use GitHub **private vulnerability reporting** (repo → Security → Report a
vulnerability). Please do not open public issues for security reports.

The attack surface of this project is intentionally small: the game is
offline-only, does not network (SPECS §2), reads/writes only its own
config/save files under the paths of SPECS §9, and ships self-contained
binaries. In scope: crafted config/save files (parser safety), path handling,
asset parsing, bundle integrity. Out of scope: anything requiring the game to
talk to the internet — by design it cannot.
