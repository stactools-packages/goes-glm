import json
import os.path
import shutil
from tempfile import TemporaryDirectory
from typing import Callable, List

from click import Command, Group
from stactools.testing.cli_test import CliTestCase

from stactools.goes_glm.commands import create_goesglm_command

SRC_FOLDER = "./tests/data-files/"

TEST_FILES = [
    "OR_GLM-L2-LCFA_G16_s20203662359400_e20210010000004_c20210010000030",
    "OR_GLM-L2-LCFA_G17_s20221542100000_e20221542100200_c20221542100217",
    "OR_GLM-L2-LCFA_G18_s20230261900000_e20230261900200_c20230261900213",
]
LICENSE = "https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id=gov.noaa.ncdc:C01527"


class CommandsTest(CliTestCase):
    def create_subcommand_functions(self) -> List[Callable[[Group], Command]]:
        return [create_goesglm_command]

    def test_create_collection(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            destination = os.path.join(tmp_dir, "collection.json")

            result = self.run_command(
                f"goes-glm create-collection {destination} "
                f"--start_time 2022-01-01T00:00:00Z --license '{LICENSE}'"
            )

            self.assertEqual(result.exit_code, 0, msg="\n{}".format(result.output))

            jsons = [p for p in os.listdir(tmp_dir) if p.endswith(".json")]
            self.assertEqual(len(jsons), 1)

            collection = {}
            with open(destination) as f:
                collection = json.load(f)

            self.assertEqual(collection["id"], "goes-glm")

    def test_create_item(self) -> None:
        for id in TEST_FILES:
            with self.subTest(id=id):
                with TemporaryDirectory() as tmp_dir:
                    src_data_filename = f"{id}.nc"
                    stac_filename = f"{id}.json"

                    src_collection = os.path.join(SRC_FOLDER, "collection.json")
                    src_data_file = os.path.join(SRC_FOLDER, src_data_filename)
                    dest_data_file = os.path.join(tmp_dir, src_data_filename)
                    shutil.copyfile(src_data_file, dest_data_file)

                    dest_stac = os.path.join(tmp_dir, stac_filename)

                    result = self.run_command(
                        f"goes-glm create-item {dest_data_file} {dest_stac} "
                        f"--collection {src_collection} "
                        f"--appendctime TRUE"
                    )
                    self.assertEqual(
                        result.exit_code, 0, msg="\n{}".format(result.output)
                    )

                    files = os.listdir(tmp_dir)
                    jsons = [p for p in files if p.endswith(".json")]
                    self.assertEqual(len(jsons), 1)

                    item = {}
                    with open(dest_stac) as f:
                        item = json.load(f)

                    self.assertEqual(item["id"], id)
