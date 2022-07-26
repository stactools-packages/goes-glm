import os.path
import shutil
import unittest

# from datetime import datetime, timezone
from tempfile import TemporaryDirectory
from typing import Any, Dict, List, Optional

from pystac import Collection, Item

from stactools.goes_glm import stac

LICENSE = "https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id=gov.noaa.ncdc:C01527"
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
        "nogeoparquet": False,
        "nonetcdf": False,
    },
    {
        "nogeoparquet": True,
        "nonetcdf": False,
    },
    {
        "nogeoparquet": False,
        "nonetcdf": True,
    },
]

TEST_ITEMS: List[Dict[str, Any]] = [
    {
        "id": "OR_GLM-L2-LCFA_G16_s20203662359400_e20210010000004_c20210010000030",
        "nogeoparquet": False,
        "nonetcdf": False,
        "collection": "./tests/data-files/collection.json",
    },
    {
        "id": "OR_GLM-L2-LCFA_G16_s20203662359400_e20210010000004_c20210010000030",
        "nogeoparquet": True,
        "nonetcdf": False,
    },
    {
        "id": "OR_GLM-L2-LCFA_G17_s20221542100000_e20221542100200_c20221542100217",
        "nogeoparquet": False,
        "nonetcdf": True,
    },
]


class StacTest(unittest.TestCase):
    def test_create_collection(self) -> None:
        for test_data in TEST_COLLECTIONS:
            with self.subTest(test_data=test_data):
                id: str = test_data["id"] if "id" in test_data else "goes-glm"
                nogeoparquet: bool = test_data["nogeoparquet"]
                nonetcdf: bool = test_data["nonetcdf"]

                # Write tests for each for the creation of a STAC Collection
                # Create the STAC Collection...
                collection = stac.create_collection(LICENSE, **test_data)
                collection.set_self_href("")
                collection.validate()
                collection_dict = collection.to_dict()

                self.assertEqual(collection.id, id)

                self.assertTrue("item_assets" in collection_dict)
                assets: Dict[str, Dict[str, Any]] = collection_dict["item_assets"]

                # Check geoparquet assets
                for key in PARQUET_KEYS:
                    self.assertEqual(key in assets, not nogeoparquet)
                    if not nogeoparquet:
                        asset = assets[key]
                        self.assertEqual(asset["type"], PARQUET_MEDIA_TYPE)

                # Check netCDF asset
                if nonetcdf:
                    self.assertFalse("netcdf" in assets)
                else:
                    self.assertTrue("netcdf" in assets)
                    asset = assets["netcdf"]
                    self.assertEqual(asset["type"], NETCDF_MEDIA_TYPE)

                # todo: more tests #6

    def test_create_item(self) -> None:
        for test_data in TEST_ITEMS:
            with self.subTest(test_data=test_data):
                id: str = test_data["id"]
                del test_data["id"]
                nogeoparquet: bool = test_data["nogeoparquet"]
                nonetcdf: bool = test_data["nonetcdf"]

                item: Optional[Item] = None
                with TemporaryDirectory() as tmp_dir:
                    src_data_file = os.path.join("./tests/data-files/", f"{id}.nc")
                    dest_data_file = os.path.join(tmp_dir, f"{id}.nc")
                    shutil.copyfile(src_data_file, dest_data_file)
                    test_data["asset_href"] = dest_data_file

                    if "collection" in test_data:
                        test_data["collection"] = Collection.from_file(
                            test_data["collection"]
                        )

                    item = stac.create_item(**test_data)
                    item.validate()
                    # item_dict = collection.to_dict()

                    self.assertIsNotNone(item)
                    self.assertEqual(item.id, id)

                    # Check geoparquet assets
                    for key in PARQUET_KEYS:
                        self.assertEqual(key in item.assets, not nogeoparquet)
                        if not nogeoparquet:
                            asset = item.assets[key].to_dict()
                            self.assertEqual(asset["type"], PARQUET_MEDIA_TYPE)

                    # Check netCDF asset
                    if nonetcdf:
                        self.assertFalse("netcdf" in item.assets)
                    else:
                        self.assertTrue("netcdf" in item.assets)
                        asset = item.assets["netcdf"].to_dict()
                        self.assertEqual(asset["type"], NETCDF_MEDIA_TYPE)

                    # todo: more tests #6
