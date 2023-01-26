#!/usr/bin/env python

import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from pystac import CatalogType
from stactools.core import copy

from stactools.goes_glm import stac

root = Path(__file__).parents[1]
examples = root / "examples"
data_files = root / "tests" / "data-files"

shutil.rmtree(examples, ignore_errors=True)
collection = stac.create_collection("proprietary")
with TemporaryDirectory() as temporary_directory:
    for i, filename in enumerate(
        (
            "OR_GLM-L2-LCFA_G16_s20181591447400_e20181591448000_c20181591448028.nc",
            "OR_GLM-L2-LCFA_G17_s20182831047000_e20182831047200_c20182831047223.nc",
            "OR_GLM-L2-LCFA_G17_s20200160612000_e20200160612110_c20200160612335.nc",
            "OR_GLM-L2-LCFA_G18_s20230261900000_e20230261900200_c20230261900213.nc",
        )
    ):
        directory = Path(temporary_directory) / str(i)
        directory.mkdir()
        path = directory / filename
        shutil.copy(data_files / filename, path)
        item = stac.create_item(str(path))
        collection.add_item(item)

    collection.normalize_hrefs(str(examples))
    copy.move_all_assets(collection)

collection.save(catalog_type=CatalogType.SELF_CONTAINED)
