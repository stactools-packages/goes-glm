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
    },
    {
        "name": "OR_GLM-L2-LCFA_G17_s20200160612000_e20200160612110_c20200160612335",
        "appendctime": True,
    },
]


class StacTest(unittest.TestCase):
    def test_create_collection(self) -> None:
        for test_data in TEST_COLLECTIONS:
            with self.subTest(test_data=test_data):
                id: str = test_data["id"] if "id" in test_data else "goes-glm"
                nogeoparquet: bool = (
                    test_data["nogeoparquet"] if "nogeoparquet" in test_data else False
                )
                nonetcdf: bool = (
                    test_data["nonetcdf"] if "nonetcdf" in test_data else False
                )

                collection = stac.create_collection(LICENSE, **test_data)
                collection.set_self_href("")
                collection.validate()
                collection_dict = collection.to_dict()

                self.assertEqual(collection.id, id)

                self.assertEqual(collection_dict["sci:doi"], "10.7289/V5KH0KK6")
                self.assertTrue("sci:citation" in collection_dict)

                self.assertTrue("summaries" in collection_dict)
                summaries = collection_dict["summaries"]
                self.assertEqual(summaries["mission"], ["GOES"])
                self.assertEqual(summaries["constellation"], ["GOES"])
                self.assertEqual(summaries["platform"], ["GOES-16", "GOES-17"])
                self.assertEqual(summaries["instruments"], ["FM1", "FM2"])
                self.assertEqual(summaries["gsd"], [8000])
                self.assertEqual(summaries["processing:level"], ["L2"])
                self.assertEqual(summaries["goes:orbital-slot"], ["West", "East"])

                self.assertTrue("item_assets" in collection_dict)
                assets: Dict[str, Dict[str, Any]] = collection_dict["item_assets"]

                asset_count = 4
                if nogeoparquet:
                    asset_count -= 3
                if nonetcdf:
                    asset_count -= 1
                self.assertEqual(len(assets), asset_count)

                # Check geoparquet assets
                for key in PARQUET_KEYS:
                    self.assertEqual(key in assets, not nogeoparquet)
                    if not nogeoparquet:
                        asset = assets[key]
                        self.assertEqual(asset["type"], PARQUET_MEDIA_TYPE)
                        self.assertEqual(asset["table:primary_geometry"], "geometry")

                # Check netCDF asset
                if nonetcdf:
                    self.assertFalse("netcdf" in assets)
                else:
                    self.assertTrue("netcdf" in assets)
                    asset = assets["netcdf"]
                    self.assertEqual(asset["type"], NETCDF_MEDIA_TYPE)
                    self.assertFalse("table:primary_geometry" in asset)

    def test_create_item(self) -> None:
        for test_data in TEST_ITEMS:
            with self.subTest(test_data=test_data):
                name: str = test_data["name"]
                id: str = test_data["id"] if "id" in test_data else name
                nogeoparquet: bool = (
                    test_data["nogeoparquet"] if "nogeoparquet" in test_data else False
                )
                nonetcdf: bool = (
                    test_data["nonetcdf"] if "nonetcdf" in test_data else False
                )
                appendctime: bool = (
                    test_data["appendctime"] if "appendctime" in test_data else False
                )

                collection: Optional[Collection] = None
                if "collection" in test_data:
                    collection = Collection.from_file(test_data["collection"])

                item: Optional[Item] = None
                with TemporaryDirectory() as tmp_dir:
                    src_data_file = os.path.join("./tests/data-files/", f"{name}.nc")
                    dest_data_file = os.path.join(tmp_dir, f"{name}.nc")
                    shutil.copyfile(src_data_file, dest_data_file)

                    del test_data["name"]
                    if "id" in test_data:
                        del test_data["id"]
                    test_data["asset_href"] = dest_data_file
                    test_data["collection"] = collection

                    item = stac.create_item(**test_data)
                    item.validate()

                if id.find("_G16_") != -1:
                    platform = 16
                elif id.find("_G17_") != -1:
                    platform = 17
                else:
                    platform = 18

                self.assertIsNotNone(item)
                self.assertEqual(item.id, name if appendctime else id)
                if collection is not None:
                    self.assertEqual(item.collection_id, collection.id)
                else:
                    self.assertIsNone(item.collection_id)

                self.assertTrue("datetime" in item.properties)
                self.assertTrue("start_datetime" in item.properties)
                self.assertTrue("end_datetime" in item.properties)
                self.assertEqual(item.properties["mission"], "GOES")
                self.assertEqual(item.properties["constellation"], "GOES")
                self.assertEqual(item.properties["platform"], f"GOES-{platform}")
                instrument = platform - 15
                self.assertEqual(item.properties["instruments"], [f"FM{instrument}"])
                self.assertEqual(item.properties["gsd"], 8000)
                self.assertEqual(item.properties["goes:system-environment"], "OR")
                if (
                    id
                    == "OR_GLM-L2-LCFA_G16_s20203662359400_e20210010000004_c20210010000030"
                ):
                    self.assertEqual(item.properties["goes:orbital-slot"], "East")
                elif (
                    id
                    == "OR_GLM-L2-LCFA_G17_s20221542100000_e20221542100200_c20221542100217"
                ):
                    self.assertEqual(item.properties["goes:orbital-slot"], "West")
                else:
                    self.assertTrue("goes:orbital-slot" in item.properties)
                self.assertEqual(item.properties["proj:epsg"], 4326)
                self.assertEqual(item.properties["processing:level"], "L2")

                asset_count = 4
                if nogeoparquet:
                    asset_count -= 3
                if nonetcdf:
                    asset_count -= 1
                self.assertEqual(len(item.assets), asset_count)

                # Check geoparquet assets
                for key in PARQUET_KEYS:
                    self.assertEqual(key in item.assets, not nogeoparquet)
                    if not nogeoparquet:
                        asset = item.assets[key].to_dict()
                        self.assertEqual(asset["type"], PARQUET_MEDIA_TYPE)
                        self.assertTrue("title" in asset)
                        self.assertFalse("created" in asset)
                        self.assertFalse("cube:dimensions" in asset)
                        self.assertFalse("cube:variables" in asset)
                        self.assertTrue("table:row_count" in asset)
                        self.assertEqual(asset["table:primary_geometry"], "geometry")
                        self.assertTrue("table:columns" in asset)
                        hasGeometryCol = False
                        for col in asset["table:columns"]:
                            self.assertTrue("name" in col)
                            self.assertTrue("type" in col)
                            if col["name"] == "geometry":
                                hasGeometryCol = True
                        self.assertTrue(hasGeometryCol)

                # Check netCDF asset
                if nonetcdf:
                    self.assertFalse("netcdf" in item.assets)
                else:
                    self.assertTrue("netcdf" in item.assets)
                    asset = item.assets["netcdf"].to_dict()
                    self.assertEqual(asset["type"], NETCDF_MEDIA_TYPE)
                    self.assertTrue("title" in asset)
                    self.assertTrue("created" in asset)
                    self.assertFalse("table:row_count" in asset)
                    self.assertFalse("table:columns" in asset)
                    self.assertFalse("table:primary_geometry" in asset)

                    self.assertTrue("cube:dimensions" in asset)
                    dims = asset["cube:dimensions"]
                    self.assertEqual(len(dims), 6)
                    for dim in dims.values():
                        self.assertTrue("type" in dim)
                        self.assertTrue("extent" in dim)

                    self.assertTrue("cube:variables" in asset)
                    vars = asset["cube:variables"]
                    # Some older files have 45 variables, newer ones have 48. See
                    # https://github.com/stactools-packages/goes-glm/issues/17#issuecomment-1241875842
                    self.assertTrue(len(vars) == 45 or len(vars) == 48)
                    for var in vars.values():
                        self.assertTrue("dimensions" in var)
                        self.assertTrue("type" in var)
                        self.assertTrue("description" in var)
