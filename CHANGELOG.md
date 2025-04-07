# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project attempts to match the major and minor versions of
[stactools](https://github.com/stac-utils/stactools) and increments the patch
number as needed.

## [Unreleased]

### Added
- Added support for GOES-19 ([#29](https://github.com/stactools-packages/goes-glm/pull/29))

## [0.2.3]

### Fixed

- Metadata in setup.cfg ([#28](https://github.com/stactools-packages/goes-glm/pull/28))

## [0.2.2]

### Added

- Support for GOES-18 ([#26](https://github.com/stactools-packages/goes-glm/pull/26))

## [0.2.1]

### Changed

- Updated to latest stactools-packages template (updates dependencies, etc.)

### Fixed

- Fixed a typo in the variable detection

## [0.2.0]

### Added

- New option `fixnetcdf` for Item creation
  [#17](https://github.com/stactools-packages/goes-glm/issues/17)
- New option `appendctime` for Item creation
  [#19](https://github.com/stactools-packages/goes-glm/issues/19)
- Handle GOES-Test correctly

### Changed

- Use snake case instead of kebab case in all `goes:` field names
- `goes-glm:` prefiexed fields use now the `goes:` prefix

### Deprecated

- Nothing.

### Removed

- `goes-glm:product_time` doesn't get exported any longer.
  Use STAC's native datetime fields instead.

### Fixed

- Handle missing `...frame_time_offset...` variables correctly
- Handle inconsistencies in the `..._count` variables better
- Handle netCDF files with no events/flashes correctly
- Added GOES extension in `stac_extensions`

## [0.1.0]

- First release

[Unreleased]: <https://github.com/stactools-packages/goes-glm/tree/main/>
[0.2.2]: <https://github.com/stactools-packages/goes-glm/compare/v0.2.1..v0.2.2>
[0.2.1]: <https://github.com/stactools-packages/goes-glm/compare/v0.2.0..v0.2.1>
[0.2.0]: <https://github.com/stactools-packages/goes-glm/compare/v0.1.0..v0.2.0>
[0.1.0]: <https://github.com/stactools-packages/goes-glm/tree/v0.1.0/>
