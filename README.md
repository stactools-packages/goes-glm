# stactools-goes-glm

[![PyPI](https://img.shields.io/pypi/v/stactools-goes-glm)](https://pypi.org/project/stactools-goes-glm/)

- Name: goes-glm
- Package: `stactools.goes_glm`
- PyPI: <https://pypi.org/project/stactools-goes-glm/>
- Owner: @m-mohr
- Dataset homepage:
  - <https://www.goes-r.gov/spacesegment/glm.html>
  - <https://ghrc.nsstc.nasa.gov/lightning/overview_glm.html>
- STAC extensions used:
  - [datacube](https://github.com/stac-extensions/datacube/) (for netCDF only)
  - [GOES](https://github.com/stac-extensions/goes/)
  - [processing](https://github.com/stac-extensions/processing/)
  - [proj](https://github.com/stac-extensions/projection/)
  - [table](https://github.com/stac-extensions/table/) (for geoparquet only)
- Extra fields:
  - Prefix `goes:`: As defined in the [GOES extension](https://github.com/stac-extensions/goes/).
    All variables with valid scalar values / without dimensions are added to
    the Item properties with a `goes:` prefix. The variable name is used as
    the property key after the prefix, e.g. `goes:event_count`.

A stactools package for the Geostationary Lightning Mapper (GLM) dataset, which
is on the GOES-16/R, GOES-17/S, and GOES-18/T satellites. GLM detects all forms
of lightning during both day and night, continuously, with a high spatial
resolution and detection efficiency.

This package can generate STAC files from netCDF files and that either link to
the original netCDF files or to geoparquet files.

## STAC Examples

- [Collection](examples/collection.json)
- [Item (GOES-16/R)](./examples/OR_GLM-L2-LCFA_G16_s20181591447400_e20181591448000/OR_GLM-L2-LCFA_G16_s20181591447400_e20181591448000.json)
- [Item (GOES-17/S)](./examples/OR_GLM-L2-LCFA_G17_s20200160612000_e20200160612110/OR_GLM-L2-LCFA_G17_s20200160612000_e20200160612110.json)
- [Item (GOES-17/S (Test) before drifting to the final location)](./examples/OR_GLM-L2-LCFA_G17_s20182831047000_e20182831047200/OR_GLM-L2-LCFA_G17_s20182831047000_e20182831047200.json)
- [Item (GOES-18/T)](./examples/OR_GLM-L2-LCFA_G18_s20230261900000_e20230261900200/OR_GLM-L2-LCFA_G18_s20230261900000_e20230261900200.json)
- [Browse the example in a human-readable form](https://radiantearth.github.io/stac-browser/#/external/raw.githubusercontent.com/stactools-packages/goes-glm/main/examples/collection.json)

## Installation

```shell
pip install stactools-goes-glm
```

## Command-line Usage

Use `stac goes-glm --help` to see all subcommands and options.

### Collection

Create a collection:

```shell
stac goes-glm create-collection collection.json --license=https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id=gov.noaa.ncdc:C01527
```

Get information about all options for collection creation:

```shell
stac goes-glm create-collection --help
```

### Item

Create an item with a netCDF and multiple geoparquet asset:

```shell
stac goes-glm create-item OR_GLM-L2-LCFA_G16_s20203662359400_e20210010000004_c20210010000030.nc item.json --collection collection.json
```

Create an item with only geoparquet assets:

```shell
stac goes-glm create-item OR_GLM-L2-LCFA_G17_s20221542100000_e20221542100200_c20221542100217.nc item.json --collection collection.json --nonetcdf TRUE
```

Get information about all options for item creation:

```shell
stac goes-glm create-item --help
```

## Contributing

We use [pre-commit](https://pre-commit.com/) to check any changes.
To set up your development environment:

```shell
pip install -e .
pip install -r requirements-dev.txt
pre-commit install
```

To check all files:

```shell
pre-commit run --all-files
```

To run the tests:

```shell
pytest -vv
```
