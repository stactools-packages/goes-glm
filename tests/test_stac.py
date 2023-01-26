import os.path
import shutil
from tempfile import TemporaryDirectory
from typing import Any, Dict, List, Optional

import pytest
from pystac import Collection, Item

from stactools.goes_glm import stac

LICENSE = (
    "https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso"
    "?id=gov.noaa.ncdc:C01527"
)
THUMBNAIL = "https://example.com/thumb.png"

PARQUET_MEDIA_TYPE = "application/x-parquet"
PARQUET_KEYS = [
    "geoparquet_events",
    "geoparquet_groups",
    "geoparquet_flashes",
]
NETCDF_MEDIA_TYPE = "application/netcdf"

TEST_COLLECTIONS: List[Dict[str, Any]] = [
    {
        "id": "goes-glm",
        "thumbnail": THUMBNAIL,
        "start_time": "2020-06-06T12:12:12.12Z",
    },
    {
        "nogeoparquet": True,
    },
    {
        "nonetcdf": True,
    },
]

TEST_ITEMS: List[Dict[str, Any]] = [
    {
        "name": "OR_GLM-L2-LCFA_G16_s20203662359400_e20210010000004_c20210010000030",
        "id": "OR_GLM-L2-LCFA_G16_s20203662359400_e20210010000004",
        "collection": "./tests/data-files/collection.json",
    },
    {
        "name": "OR_GLM-L2-LCFA_G16_s20203662359400_e20210010000004_c20210010000030",
        "id": "OR_GLM-L2-LCFA_G16_s20203662359400_e20210010000004",
        "nogeoparquet": True,
    },
    {
        "name": "OR_GLM-L2-LCFA_G17_s20221542100000_e20221542100200_c20221542100217",
        "nonetcdf": True,
        "appendctime": True,
    },
    {
        "name": "OR_GLM-L2-LCFA_G16_s20181591447400_e20181591448000_c20181591448028",
        "appendctime": True,
    },
    {
        "name": "OR_GLM-L2-LCFA_G16_s20182901026200_e20182901026400_c20182901026423",
        "appendctime": True,
    },
    {
        "name": "OR_GLM-L2-LCFA_G16_s20182980537000_e20182980537200_c20182980537216",
        "appendctime": True,
    },
    {
        "name": "OR_GLM-L2-LCFA_G16_s20210820633400_e20210820634005_c20210820634025",
        "id": "OR_GLM-L2-LCFA_G16_s20210820633400_e20210820634005",
    },
    {
        "name": "OR_GLM-L2-LCFA_G17_s20182831047000_e20182831047200_c20182831047223",
        "appendctime": True,
        "test": True,
    },
    {
        "name": "OR_GLM-L2-LCFA_G17_s20200160612000_e20200160612110_c20200160612335",
        "appendctime": True,
    },
]


@pytest.mark.parametrize("options", TEST_COLLECTIONS)
def test_create_collection(options: Dict[str, Any]) -> None:
    id: str = options["id"] if "id" in options else "goes-glm"
    nogeoparquet: bool = options["nogeoparquet"] if "nogeoparquet" in options else False
    nonetcdf: bool = options["nonetcdf"] if "nonetcdf" in options else False

    collection = stac.create_collection(LICENSE, **options)
    collection.set_self_href("")
    collection.validate()
    collection_dict = collection.to_dict()

    assert collection.id == id

    assert collection_dict["sci:doi"] == "10.7289/V5KH0KK6"
    assert "sci:citation" in collection_dict

    assert "summaries" in collection_dict
    summaries = collection_dict["summaries"]
    assert summaries["mission"] == ["GOES"]
    assert summaries["constellation"] == ["GOES"]
    assert summaries["platform"] == ["GOES-16", "GOES-17"]
    assert summaries["instruments"] == ["FM1", "FM2"]
    assert summaries["gsd"] == [8000]
    assert summaries["processing:level"] == ["L2"]
    assert summaries["goes:orbital_slot"] == ["West", "East", "Test"]

    assert "item_assets" in collection_dict
    assets: Dict[str, Dict[str, Any]] = collection_dict["item_assets"]

    asset_count = 4
    if nogeoparquet:
        asset_count -= 3
    if nonetcdf:
        asset_count -= 1
    assert len(assets) == asset_count

    # Check geoparquet assets
    for key in PARQUET_KEYS:
        assert (key in assets) == (not nogeoparquet)
        if not nogeoparquet:
            asset = assets[key]
            assert asset["type"] == PARQUET_MEDIA_TYPE
            assert asset["table:primary_geometry"] == "geometry"

    # Check netCDF asset
    if nonetcdf:
        assert "netcdf" not in assets
    else:
        assert "netcdf" in assets
        asset = assets["netcdf"]
        assert asset["type"] == NETCDF_MEDIA_TYPE
        assert "table:primary_geometry" not in asset


@pytest.mark.parametrize("options", TEST_ITEMS)
def test_create_item(options: Dict[str, Any]) -> None:
    name: str = options["name"]
    id: str = options["id"] if "id" in options else name
    nogeoparquet: bool = options["nogeoparquet"] if "nogeoparquet" in options else False
    nonetcdf: bool = options["nonetcdf"] if "nonetcdf" in options else False
    appendctime: bool = options["appendctime"] if "appendctime" in options else False
    goes_test: bool = options["test"] if "test" in options else False

    collection: Optional[Collection] = None
    if "collection" in options:
        collection = Collection.from_file(options["collection"])

    item: Optional[Item] = None
    with TemporaryDirectory() as tmp_dir:
        src_data_file = os.path.join("./tests/data-files/", f"{name}.nc")
        dest_data_file = os.path.join(tmp_dir, f"{name}.nc")
        shutil.copyfile(src_data_file, dest_data_file)

        del options["name"]
        if "test" in options:
            del options["test"]
        if "id" in options:
            del options["id"]
        options["asset_href"] = dest_data_file
        options["collection"] = collection

        item = stac.create_item(**options)
        item.validate()

    if id.find("_G16_") != -1:
        platform = 16
    elif id.find("_G17_") != -1:
        platform = 17
    else:
        platform = 18

    assert item is not None
    assert item.id == name if appendctime else id
    if collection is not None:
        assert item.collection_id == collection.id
    else:
        assert item.collection_id is None

    assert "datetime" in item.properties
    assert "start_datetime" in item.properties
    assert "end_datetime" in item.properties
    assert item.properties["mission"] == "GOES"
    assert item.properties["constellation"] == "GOES"
    assert item.properties["platform"] == f"GOES-{platform}"
    instrument = platform - 15
    assert item.properties["instruments"] == [f"FM{instrument}"]
    assert item.properties["gsd"] == 8000
    assert item.properties["goes:system_environment"] == "OR"
    if goes_test:
        assert item.properties["goes:orbital_slot"] == "Test"
    elif platform == 16:
        assert item.properties["goes:orbital_slot"] == "East"
    elif platform == 17:
        assert item.properties["goes:orbital_slot"] == "West"
    else:
        assert "goes:orbital_slot" in item.properties
    assert item.properties["proj:epsg"] == 4326
    assert item.properties["processing:level"] == "L2"

    asset_count = 4
    if nogeoparquet:
        asset_count -= 3
    if nonetcdf:
        asset_count -= 1
    assert len(item.assets) == asset_count

    # Check geoparquet assets
    for key in PARQUET_KEYS:
        assert (key in item.assets) == (not nogeoparquet)
        if not nogeoparquet:
            asset = item.assets[key].to_dict()
            assert asset["type"] == PARQUET_MEDIA_TYPE
            assert "title" in asset
            assert "created" not in asset
            assert "cube:dimensions" not in asset
            assert "cube:variables" not in asset
            assert "table:row_count" in asset
            assert asset["table:primary_geometry"] == "geometry"
            assert "table:columns" in asset
            cols = []
            for col in asset["table:columns"]:
                assert "name" in col
                assert "type" in col
                cols.append(col["name"])
            # check for geometry column
            assert "geometry" in cols
            # check for datetime columns
            if key == "geoparquet_flashes":
                assert "time_of_first_event" in cols
                assert "time_of_last_event" in cols
            else:
                assert "time" in cols

    # Check netCDF asset
    if nonetcdf:
        assert "netcdf" not in item.assets
    else:
        assert "netcdf" in item.assets
        asset = item.assets["netcdf"].to_dict()
        assert asset["type"] == NETCDF_MEDIA_TYPE
        assert "title" in asset
        assert "created" in asset
        assert "table:row_count" not in asset
        assert "table:columns" not in asset
        assert "table:primary_geometry" not in asset

        assert "cube:dimensions" in asset
        dims = asset["cube:dimensions"]
        assert len(dims) == 6
        for dim in dims.values():
            assert "type" in dim
            assert "extent" in dim

        assert "cube:variables" in asset
        vars = asset["cube:variables"]
        # Some older files have 45 variables, newer ones have 48. See
        # https://github.com/stactools-packages/goes-glm/issues/17#issuecomment-1241875842
        assert len(vars) == 45 or len(vars) == 48
        for var in vars.values():
            assert "dimensions" in var
            assert "type" in var
            assert "description" in var
