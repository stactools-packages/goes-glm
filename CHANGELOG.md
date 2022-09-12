# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/). This project attempts to match the major and minor versions of [stactools](https://github.com/stac-utils/stactools) and increments the patch number as needed.

## [Unreleased]

### Added

- New option `fixnetcdf` (see issue [#17](https://github.com/stactools-packages/goes-glm/issues/17) for details)

### Deprecated

- Nothing.

### Removed

- Nothing.

### Fixed

- Handle missing `...frame_time_offset...` variables correctly
- Handle inconsistencies in the `..._count` variables better
- Don't throw an error if the orbital slot is GOES-Test
- Handle netCDF files with no events/flashes correctly

## [0.1.0]

- First release

[Unreleased]: <https://github.com/stactools-packages/goes-glm/tree/main/>
[0.1.0]: <https://github.com/stactools-packages/goes-glm/tree/v0.1.0/>
