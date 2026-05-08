# Changelog

## 2026-05-05 - 03:29
### Fixed
- Corrected method call in `graphics.py`: `Vec2.length` replaced with `Vec2.length()`.
- Verified method types via diagnostic scratch testing.

## 2026-05-05 - 03:27
### Fixed
- Corrected attribute name in `graphics.py`: `Vec2.mag` replaced with `Vec2.length`.
- Verified `pyglet.math.Vec2` attribute availability via scratch testing.

## 2026-05-05 - 03:25
### Fixed
- Resolved `AttributeError` in `graphics.py` by replacing non-existent `from_magnitude` with `normalize` logic in `ArrowLine`.
- Added safety check for zero-length vectors in arrow tine calculations.

## 2026-05-05 - 03:21
### Added
- Comprehensive educational commentary across all core modules.
- Explicit attribution for refactoring and maintenance.
- Pyglet 2.1.14+ compatibility assurance.

### Changed
- Refactored `agent.py` to fix `delta` scope issues and improve steering logic readability.
- Updated `graphics.py` to ensure modern `pyglet.shapes` and `pyglet.math` integration.
- Standardised documentation and code style across the project.
- Updated project manifest version to `2026.5.5.0321`.
