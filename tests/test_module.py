import unittest

import stactools.goes_glm


class TestModule(unittest.TestCase):
    def test_version(self) -> None:
        self.assertIsNotNone(stactools.goes_glm.__version__)
