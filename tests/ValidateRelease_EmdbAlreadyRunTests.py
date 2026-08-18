import os
import shutil
import tempfile
import time
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


def touch(fname: str, times: Optional[Tuple[Union[int, float], Union[int, float]]] = None) -> None:
    with open(fname, "a"):
        os.utime(fname, times)


class ModifiedFolderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.patcher = patch("wwpdb.utils.config.ConfigInfoApp.ConfigInfo", side_effect=StandardConfig)

        self.patcher.start()

        self.input_dir = tempfile.mkdtemp()
        self.pdbid = "1cbs"
        self.pdbid_hash = self.pdbid[1:3]
        self.emdb = "EMD-1234"
        self.pdbid_file = os.path.join(self.input_dir, self.pdbid + ".cif")
        self.emdb_file = os.path.join(self.input_dir, self.emdb + ".xml")
        touch(self.pdbid_file)
        touch(self.emdb_file)
        self.output_dir = tempfile.mkdtemp()
        # self.pdb_output_folder =  os.path.join(self.output_dir, self.pdbid_hash, self.pdbid)
        self.emdb_output_folder = os.path.join(self.output_dir, self.emdb)
        self.rv = runValidation()
        self.rv.setOutputRoot(self.output_dir)
        time.sleep(1)
        os.makedirs(self.emdb_output_folder)

    def tearDown(self) -> None:
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir, ignore_errors=True)
        if os.path.exists(self.input_dir):
            shutil.rmtree(self.input_dir, ignore_errors=True)

        self.patcher.stop()

    def test_always_run(self) -> None:
        self.rv.setPdbId(self.pdbid)
        self.rv.setAlwaysRecalculate(True)
        ret = self.rv.check_emdb_already_run()
        # expected True - is modified - run validation
        self.assertTrue(ret)

    def test_pdb_not_modified(self) -> None:
        self.rv.setPdbId(self.pdbid)
        self.rv.setModelPath(self.pdbid_file)
        self.rv.setEmdbOutputFolder(self.emdb_output_folder)
        ret = self.rv.check_emdb_already_run()
        # expected False - not modified - don't run validation
        self.assertFalse(ret)

    def test_emdb_not_modified(self) -> None:
        self.rv.setEmdbId(self.emdb)
        self.rv.setEmXmlPath(self.emdb_file)
        self.rv.setEmdbOutputFolder(self.emdb_output_folder)
        ret = self.rv.check_emdb_already_run()
        # expected False - not modified - don't run validation
        self.assertFalse(ret)

    def test_pdb_modified(self) -> None:
        self.rv.setPdbId(self.pdbid)
        self.rv.setModelPath(self.pdbid_file)
        self.rv.setEmdbOutputFolder(self.emdb_output_folder)
        touch(self.pdbid_file)
        ret = self.rv.check_emdb_already_run()
        # expected False - EMDB not modified - do not run validation
        self.assertFalse(ret)

    def test_emdb_modified(self) -> None:
        self.rv.setEmdbId(self.emdb)
        self.rv.setEmXmlPath(self.emdb_file)
        self.rv.setEmdbOutputFolder(self.emdb_output_folder)
        time.sleep(1)
        touch(self.emdb_file)
        ret = self.rv.check_emdb_already_run()
        # expected True - modified - do run validation
        self.assertTrue(ret)

    def test_pdb_and_emdb_with_pdb_modified(self) -> None:
        self.rv.setPdbId(self.pdbid)
        self.rv.setEmdbId(self.emdb)
        self.rv.setModelPath(self.pdbid_file)
        self.rv.setEmdbOutputFolder(self.emdb_output_folder)
        touch(self.pdbid_file)
        ret = self.rv.check_emdb_already_run()
        # expected False - EMDB not modified - do not run validation
        self.assertFalse(ret)

    def test_pdb_and_emdb_with_emdb_modified(self) -> None:
        self.rv.setPdbId(self.pdbid)
        self.rv.setEmdbId(self.emdb)
        self.rv.setEmXmlPath(self.emdb_file)
        self.rv.setEmdbOutputFolder(self.emdb_output_folder)
        time.sleep(1)
        touch(self.emdb_file)
        ret = self.rv.check_emdb_already_run()
        # expected True - modified - do run validation
        self.assertTrue(ret)

    def test_output_folder_modified(self) -> None:
        self.rv.setEmdbId(self.emdb)
        self.rv.setEmXmlPath(self.emdb_file)
        self.rv.setEmdbOutputFolder(self.emdb_output_folder)
        touch(self.emdb_file)
        shutil.rmtree(self.emdb_output_folder)
        time.sleep(1)
        os.makedirs(self.emdb_output_folder)
        ret = self.rv.check_emdb_already_run()
        # expected True - modified - do run validation
        self.assertFalse(ret)


if __name__ == "__main__":  # pramga: no cover
    unittest.main()
