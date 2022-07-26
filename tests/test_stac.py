import unittest

from stactools.goes_glm import stac

LICENSE = "https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id=gov.noaa.ncdc:C01527"


class StacTest(unittest.TestCase):
    def test_create_collection(self) -> None:
        # Write tests for each for the creation of a STAC Collection
        # Create the STAC Collection...
        collection = stac.create_collection(license=LICENSE)
        collection.set_self_href("")

        # Check that it has some required attributes
        self.assertEqual(collection.id, "goes-glm")
        # self.assertEqual(collection.other_attr...

        # Validate
        # can't validate yet due to https://github.com/stac-utils/pystac/issues/845
        collection.validate()

    def test_create_item(self) -> None:
        # Write tests for each for the creation of STAC Items
        # Create the STAC Item...
        id = "OR_GLM-L2-LCFA_G16_s20203662359400_e20210010000004_c20210010000030"
        item = stac.create_item(f"tests/data-files/{id}.nc")

        # Check that it has some required attributes
        self.assertEqual(item.id, id)
        # self.assertEqual(item.other_attr...

        # Validate
        # can't validate yet due to https://github.com/stac-utils/pystac/issues/845
        item.validate()
