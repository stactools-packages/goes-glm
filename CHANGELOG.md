# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/). This project attempts to match the major and minor versions of [stactools](https://github.com/stac-utils/stactools) and increments the patch number as needed.

## [Unreleased]

## [0.2.0]

### Added

- New option `fixnetcdf` for Item creation (see issue [#17](https://github.com/stactools-packages/goes-glm/issues/17) for details)
- New option `appendctime` for Item creation (see issue [#19](https://github.com/stactools-packages/goes-glm/issues/19) for details)
- Handle GOES-Test correctly

### Deprecated

- Nothing.

### Removed

- Nothing.

### Fixed

- Handle missing `...frame_time_offset...` variables correctly
- Handle inconsistencies in the `..._count` variables better
- Handle netCDF files with no events/flashes correctly
- Enabled GOES extension in `stac_extensions`

## [0.1.0]

- First release

[Unreleased]: <https://github.com/stactools-packages/goes-glm/tree/main/>
[0.2.0]: <https://github.com/stactools-packages/goes-glm/tree/v0.2.0/>
[0.1.0]: <https://github.com/stactools-packages/goes-glm/tree/v0.1.0/>
