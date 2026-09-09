"""Test suite for local public archive released files."""

import logging
import os
import unittest
from typing import Any, Optional, cast
from unittest.mock import patch

if __package__ is None or __package__ == "":
    import sys
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import (  # type: ignore[import-not-found]  # pylint: disable=import-error
        LocalPublicArchiveFtpConfig,
        LocalPublicArchiveHttpConfig,
    )
else:
    from .commonsetup import (  # noqa: TID252  # pragma: no cover
        LocalPublicArchiveFtpConfig,
        LocalPublicArchiveHttpConfig,
    )


from wwpdb.io.locator.localFTPPathInfo import LocalFTPPathInfo

from wwpdb.apps.val_rel.utils.getFilesRelease import FileSource, getFilesRelease

logger = logging.getLogger(__name__)


class CommonTests:
    """Common tests for local public archive released files."""

    def assertTrue(self, expr: bool, msg: Optional[str] = None) -> None:
        if not expr:
            raise AssertionError(msg or "Assertion failed")

    def assertIsNotNone(self, obj: Any, msg: Optional[str] = None) -> None:
        if obj is None:
            raise AssertionError(msg or "Expected object to be not None")

    def assertIsNone(self, obj: Any, msg: Optional[str] = None) -> None:
        if obj is not None:
            raise AssertionError(msg or "Expected object to be None")

    def test_local_override(self) -> None:
        """Test that the local override is working."""
        logger.info("running test_local_override")
        local_ftp = LocalFTPPathInfo()
        pdb_path = local_ftp.get_ftp_pdb()
        emdb_path = local_ftp.get_ftp_emdb()

        self.assertIsNotNone(pdb_path, "PDB path should not be None")
        self.assertTrue(os.path.exists(pdb_path), "PDB path should exist: %s" % pdb_path)
        self.assertIsNotNone(emdb_path, "EMDB path should not be None")
        self.assertTrue(os.path.exists(emdb_path), "EMDB path should exist: %s" % emdb_path)

    def test_get_local_model(self) -> None:
        """Test that the local model files can be retrieved."""
        logger.info("running test_get_local_model")
        gfr_non_existant = getFilesRelease(pdb_id="1abc")
        self.assertIsNotNone(gfr_non_existant, "getFilesRelease instance should not be None")

        # Test non-existant entry
        model = gfr_non_existant.get_model()
        self.assertIsNone(model.path, "Model file should be None for non-existant entry")
        self.assertTrue(model.loc == FileSource.NONE)

        # Test for existing entry
        gfr = getFilesRelease(pdb_id="100d")
        model = gfr.get_model()
        self.assertIsNotNone(model.path, "Model file should not be None for existing entry")
        self.assertTrue(os.path.exists(cast("str", model.path)), "Model file should exist: %s" % model.path)

    def test_get_local_sf(self) -> None:
        """Test that the local sf files can be retrieved."""
        gfr_non_existant = getFilesRelease(pdb_id="1abc")
        self.assertIsNotNone(gfr_non_existant, "getFilesRelease instance should not be None")

        # Test non-existant entry
        sf = gfr_non_existant.get_sf().path
        self.assertIsNone(sf, "SF file should be None for non-existant entry")

        # Test for existing entry
        gfr = getFilesRelease(pdb_id="100d")
        sf = gfr.get_sf().path
        self.assertIsNotNone(sf, "SF file should not be None for existing entry")
        self.assertTrue(os.path.exists(cast("str", sf)), "SF file should exist: %s" % sf)

    def test_get_local_cs(self) -> None:
        """Test that the local cs files can be retrieved."""
        gfr_non_existant = getFilesRelease(pdb_id="1abc")
        self.assertIsNotNone(gfr_non_existant, "getFilesRelease instance should not be None")

        # Test non-existant entry
        cs = gfr_non_existant.get_cs().path
        self.assertIsNone(cs, "CS file should be None for non-existant entry")

        # Test for existing entry
        gfr = getFilesRelease(pdb_id="1d2b")
        cs = gfr.get_cs().path
        self.assertIsNotNone(cs, "CS file should not be None for existing entry")
        self.assertTrue(os.path.exists(cast("str", cs)), "CS file should exist: %s" % cs)

    def test_get_local_nmr_data(self) -> None:
        """Test that the local nmr data can be retrieved."""
        gfr_non_existant = getFilesRelease(pdb_id="1abc")
        self.assertIsNotNone(gfr_non_existant, "getFilesRelease instance should not be None")

        # Test non-existant entry
        nmr = gfr_non_existant.get_nmr_data()
        self.assertIsNone(nmr.path, "NMR data should be None for non-existant entry")

        # Test for existing entry
        gfr = getFilesRelease(pdb_id="11tg")
        nmr = gfr.get_nmr_data()
        self.assertIsNotNone(nmr.path, "NMR data should not be None for existing entry")
        self.assertTrue(os.path.exists(cast("str", nmr.path)), "NMR data should exist: %s" % nmr.path)

    def test_get_local_emdb_xml(self) -> None:
        """Test that the local emdb xml can be retrieved."""
        gfr_non_existant = getFilesRelease(emdb_id="EMD-0000")
        self.assertIsNotNone(gfr_non_existant, "getFilesRelease instance should not be None")

        # Test non-existant entry
        emdb_xml = gfr_non_existant.get_emdb_xml().path
        self.assertIsNone(emdb_xml, "EMDB XML should be None for non-existant entry")

        # Test for existing entry
        gfr = getFilesRelease(emdb_id="EMD-0001")
        emdb_xml = gfr.get_emdb_xml().path
        self.assertIsNotNone(emdb_xml, "EMDB XML should not be None for existing entry")
        self.assertTrue(os.path.exists(cast("str", emdb_xml)), "EMDB XML should exist: %s" % emdb_xml)

    def test_get_local_emdb_volume(self) -> None:
        """Test that the local emdb volume  can be retrieved."""
        gfr_non_existant = getFilesRelease(emdb_id="EMD-0000")
        self.assertIsNotNone(gfr_non_existant, "getFilesRelease instance should not be None")

        # Test non-existant entry
        emdb_volume = gfr_non_existant.get_emdb_volume().path
        self.assertIsNone(emdb_volume, "EMDB volume should be None for non-existant entry")

        # Test for existing entry
        gfr = getFilesRelease(emdb_id="EMD-10021")
        emdb_volume = gfr.get_emdb_volume().path
        self.assertIsNotNone(emdb_volume, "EMDB volume should not be None for existing entry")
        self.assertTrue(os.path.exists(cast("str", emdb_volume)), "EMDB volume should exist: %s" % emdb_volume)

    def test_get_local_emdb_fsc(self) -> None:
        """Test that the local emdb FSC file can be retrieved."""
        gfr_non_existant = getFilesRelease(emdb_id="EMD-0000")
        self.assertIsNotNone(gfr_non_existant, "getFilesRelease instance should not be None")

        # Test non-existant entry
        emdb_fsc = gfr_non_existant.get_emdb_fsc().path
        self.assertIsNone(emdb_fsc, "EMDB FSC should be None for non-existant entry")

        # Test for existing entry
        gfr = getFilesRelease(emdb_id="EMD-10021")
        emdb_fsc = gfr.get_emdb_fsc().path
        self.assertIsNotNone(emdb_fsc, "EMDB FSC should not be None for existing entry")
        self.assertTrue(os.path.exists(cast("str", emdb_fsc)), "EMDB FSC should exist: %s" % emdb_fsc)

    def test_get_local_emdb_metadata(self) -> None:
        """Test that the local emdb FSC file can be retrieved."""
        gfr_non_existant = getFilesRelease(emdb_id="EMD-0000")
        self.assertIsNotNone(gfr_non_existant, "getFilesRelease instance should not be None")

        # Test non-existant entry
        emdb_meta = gfr_non_existant.get_emdb_metadata().path
        self.assertIsNone(emdb_meta, "EMDB metadata should be None for non-existant entry")

        # Test for existing entry
        gfr = getFilesRelease(emdb_id="EMD-10021")
        emdb_meta = gfr.get_emdb_metadata().path
        self.assertIsNotNone(emdb_meta, "EMDB metadata should not be None for existing entry")
        self.assertTrue(os.path.exists(cast("str", emdb_meta)), "EMDB FSC should exist: %s" % emdb_meta)


class GetFilesReleaseLocalTests(CommonTests, unittest.TestCase):
    def setUp(self) -> None:
        patcher = patch("wwpdb.io.locator.localFTPPathInfo.ConfigInfo", side_effect=LocalPublicArchiveFtpConfig)
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher2 = patch("wwpdb.apps.val_rel.config.ValConfig.ConfigInfo", side_effect=LocalPublicArchiveFtpConfig)
        patcher2.start()
        self.addCleanup(patcher2.stop)
        patcher3 = patch("wwpdb.utils.config.ConfigInfoApp.ConfigInfo", side_effect=LocalPublicArchiveFtpConfig)
        patcher3.start()
        self.addCleanup(patcher3.stop)

        # logger.info("running setup")


class GetFilesReleaseLocalHttpTests(CommonTests, unittest.TestCase):
    """Common tests - but using the http fallback code"""

    def setUp(self) -> None:
        patcher = patch("wwpdb.io.locator.localFTPPathInfo.ConfigInfo", side_effect=LocalPublicArchiveHttpConfig)
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher2 = patch("wwpdb.apps.val_rel.config.ValConfig.ConfigInfo", side_effect=LocalPublicArchiveHttpConfig)
        patcher2.start()
        self.addCleanup(patcher2.stop)
        patcher3 = patch("wwpdb.utils.config.ConfigInfoApp.ConfigInfo", side_effect=LocalPublicArchiveHttpConfig)
        patcher3.start()
        self.addCleanup(patcher3.stop)

        # logger.info("running setup")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
