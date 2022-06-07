# stactools-goes-glm

[![PyPI](https://img.shields.io/pypi/v/stactools-goes-glm)](https://pypi.org/project/stactools-goes-glm/)

- Name: goes-glm
- Package: `stactools.goes_glm`
- PyPI: <https://pypi.org/project/stactools-goes-glm/>
- Owner: @m-mohr
- Dataset homepage: <https://www.goes-r.gov/spacesegment/glm.html> / <https://ghrc.nsstc.nasa.gov/lightning/overview_glm.html>
- STAC extensions used:
  - [raster](https://github.com/stac-extensions/raster/)
  - [proj](https://github.com/stac-extensions/projection/)
- Extra fields:
  - See [GOES GLM extension](./extension/README.md) for details

A stactools package for the Geostationary Lightning Mapper (GLM) dataset, which is on the GOES-16 (GEOS-R) satellite.
GLM detects all forms of lightning during both day and night, continuously, with a high spatial resolution and detection efficiency.

This package can generate STAC files from netCDF files and that either link to the original netCDF files or
to cloud-optimized GeoTiffs (COGs) in the original or any other EPSG projection.

## STAC Examples

- [Collection](examples/collection.json)
- [Item](examples/item.json)
- [Browse the example in a human-readable form](https://radiantearth.github.io/stac-browser/#/external/raw.githubusercontent.com/stactools-packages/goes-glm/main/examples/collection.json)

## Installation

```shell
pip install stactools-goes-glm
```

## Command-line Usage

### Collection

Create a collection, e.g. 24-hour Pass 2:

```shell
stac goes_glm create-collection collection.json
```

Get information about all options for collection creation:

```shell
stac goes_glm create-collection --help
```

### Item

Create an item for continentel US with a GRIB2 asset:

```shell
stac goes_glm create-item MRMS_MultiSensor_QPE_24H_Pass2_00.00_20220530-120000.grib2.gz item_grib.json --collection collection.json
```

Create an item for ALASKA with a COG asset converted to EPSG:3857:

```shell
stac goes_glm create-item MRMS_MultiSensor_QPE_24H_Pass2_00.00_20220530-120000.grib2.gz item.json --aoi ALASKA --collection collection.json --cog TRUE --epsg 3857
```

Get information about all options for item creation:

```shell
stac goes_glm create-item --help
```

Use `stac goes-glm --help` to see all subcommands and options.

Note: This package can only read files that contain the timestamp in the file name. It can NOT read the files that contain `latest` instead of a timestamp in the file name.

## Contributing

We use [pre-commit](https://pre-commit.com/) to check any changes.
To set up your development environment:

```shell
$ pip install -e .
$ pip install -r requirements-dev.txt
$ pre-commit install
```

To check all files:

```shell
$ pre-commit run --all-files
```

To run the tests:

```shell
$ pytest -vv
```
