import os.path
from tempfile import TemporaryDirectory
from typing import Callable, List

import pystac
from click import Command, Group
from stactools.testing.cli_test import CliTestCase

from stactools.goes_glm.commands import create_goesglm_command


class CommandsTest(CliTestCase):
    def create_subcommand_functions(self) -> List[Callable[[Group], Command]]:
        return [create_goesglm_command]

    def test_create_collection(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            # Run your custom create-collection command and validate

            # Example:
            destination = os.path.join(tmp_dir, "collection.json")

            result = self.run_command(
                f"goes-glm create-collection {destination} --id=glm --license=license.txt"
            )

            self.assertEqual(result.exit_code, 0, msg="\n{}".format(result.output))

            jsons = [p for p in os.listdir(tmp_dir) if p.endswith(".json")]
            self.assertEqual(len(jsons), 1)

            collection = pystac.read_file(destination)
            self.assertEqual(collection.id, "glm")
            # self.assertEqual(item.other_attr...

            # can't validate yet due to https://github.com/stac-utils/pystac/issues/845
            # collection.validate()

    def test_create_item(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            # Run your custom create-item command and validate

            # Example:
            id = "OR_GLM-L2-LCFA_G17_s20221542100000_e20221542100200_c20221542100217"
            infile = f"tests/data-files/{id}.nc"
            destination = os.path.join(tmp_dir, "item.json")
            result = self.run_command(f"goes-glm create-item {infile} {destination}")
            self.assertEqual(result.exit_code, 0, msg="\n{}".format(result.output))

            jsons = [p for p in os.listdir(tmp_dir) if p.endswith(".json")]
            self.assertEqual(len(jsons), 1)

            item = pystac.read_file(destination)
            self.assertEqual(item.id, id)
            # self.assertEqual(item.other_attr...

            # can't validate yet due to https://github.com/stac-utils/pystac/issues/845
            # item.validate()
