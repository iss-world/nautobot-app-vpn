# v2.0 Release Notes

This document describes all new features and changes in the release `2.0`. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Release Overview

- Raised the Nautobot compatibility floor to 3.0.x and validated against 3.0.1.
- Updated documentation, invoke defaults, and development images to match the new baseline.

## [v2.0.0] - 2024-11-28

### Changed

- Updated `pyproject.toml`, `poetry.lock`, and plugin metadata to require Nautobot 3.0.1 and Python 3.11+.
- Refreshed documentation (README, install guide, compatibility matrix, development guide) to state the new requirements.
- Aligned invoke configs and the development Dockerfile with Nautobot 3.0.1.

### Removed

- Dropped compatibility with Nautobot 2.4.x releases.
