import os
import unittest
from typing import Optional, Tuple, Union
from unittest.mock import patch

if __package__ is None or __package__ == "":
    import sys
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import StandardConfig  # type: ignore[import-not-found]  # pylint: disable=import-error
else:
    from .commonsetup import (  # noqa: TID252  # pragma: no cover
        StandardConfig,
    )

from wwpdb.apps.val_rel.ValidateRelease import runValidation


def touch(fname, times: Optional[Tuple[Union[int, float], Union[int, float]]] = None) -> None:
    with open(fname, "a"):
        os.utime(fname, times)


class OuputFolderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.patcher = patch("wwpdb.utils.config.ConfigInfoApp.ConfigInfo", side_effect=StandardConfig)

        self.patcher.start()

        self.pdbid = "1cbs"
        self.pdbid_hash = self.pdbid[1:3]
        self.emdb = "EMD-1234"
        self.output_folder = "/nfs/test"
        self.rv = runValidation()

    def tearDown(self) -> None:
        self.patcher.stop()

    def test_pdbid(self) -> None:
        output_dir = os.path.join(self.output_folder, "pdb", self.pdbid_hash, self.pdbid)
        self.rv.setPdbId(self.pdbid)
        self.rv.setOutputRoot(self.output_folder)
        self.rv.set_output_dir_and_files()
        self.assertTrue(self.rv.getEntryOutputFolder() == output_dir)

    def test_emdbid(self) -> None:
        output_dir = os.path.join(self.output_folder, "emd", self.emdb, "validation")
        self.rv.setEmdbId(self.emdb)
        self.rv.setOutputRoot(self.output_folder)
        self.rv.set_output_dir_and_files()
        self.assertTrue(self.rv.getEntryOutputFolder() == output_dir)

    def test_pdbid_and_emdbid(self) -> None:
        output_dir = os.path.join(self.output_folder, "pdb", self.pdbid_hash, self.pdbid)
        self.rv.setPdbId(self.pdbid)
        self.rv.setEmdbId(self.emdb)
        self.rv.setOutputRoot(self.output_folder)
        self.rv.set_output_dir_and_files()
        self.assertTrue(self.rv.getEntryOutputFolder() == output_dir)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
