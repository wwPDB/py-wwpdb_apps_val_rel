import shutil
import tempfile
import unittest
from unittest.mock import patch

if __package__ is None or __package__ == "":
    import sys
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import FtpStandardConfig  # type: ignore[import-not-found]  # pylint: disable=import-error
else:
    from .commonsetup import (  # noqa: TID252  # pragma: no cover
        FtpStandardConfig,
    )

from wwpdb.apps.val_rel.utils.getFilesReleaseFTP_EMDB import getFilesReleaseFtpEMDB


class TestsGettingEMDBData(unittest.TestCase):
    def setUp(self) -> None:
        self.patcher = patch("wwpdb.utils.config.ConfigInfoApp.ConfigInfo", side_effect=FtpStandardConfig)
        self.patcher2 = patch("wwpdb.apps.val_rel.config.ValConfig.ConfigInfo", side_effect=FtpStandardConfig)
        self.patcher.start()
        self.patcher2.start()

        self.temp_folder = tempfile.mkdtemp()

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_folder, ignore_errors=True)

        self.patcher.stop()
        self.patcher2.stop()

    def test_checking_header_existing_emdb(self) -> None:
        gfrf = getFilesReleaseFtpEMDB(emdbid="EMD-0070")
        # gfrf.setup_local_temp_ftp(session_path=self.temp_folder)
        ret = gfrf.check_header_on_remote_ftp()
        self.assertTrue(ret)

    def test_checking_header_invalid_emdb(self) -> None:
        gfrf = getFilesReleaseFtpEMDB(emdbid="EMD-ABCD")
        # gfrf.setup_local_temp_ftp(session_path=self.temp_folder)
        ret = gfrf.check_header_on_remote_ftp()
        self.assertFalse(ret)

    def test_getting_emdb_directory(self) -> None:
        gfrf = getFilesReleaseFtpEMDB(emdbid="EMD-0070")
        # gfrf.setup_local_temp_ftp(session_path=self.temp_folder)
        ret = gfrf.get_emdb_from_remote_ftp()
        self.assertTrue(ret)

    def test_getting_emdb_directory_invalid_emdb(self) -> None:
        gfrf = getFilesReleaseFtpEMDB(emdbid="EMD-ABCD")
        # gfrf.setup_local_temp_ftp(session_path=self.temp_folder)
        ret = gfrf.get_emdb_from_remote_ftp()
        self.assertFalse(ret)

    def test_get_local_ftp_emdb(self) -> None:
        gfrf = getFilesReleaseFtpEMDB(emdbid="EMD-0070")
        gfrf.set_local_ftp_path("")
        ret = gfrf.get_local_ftp_path()
        self.assertEqual(ret, "")

    def test_get_header_empty_local_ftp_emdb(self) -> None:
        gfrf = getFilesReleaseFtpEMDB(emdbid="EMD-0070")
        gfrf.set_local_ftp_path("/tmp")  # noqa: S108
        ret = gfrf.get_emdb_xml()
        self.assertIsNone(ret)

    def test_get_map_empty_local_ftp_emdb(self) -> None:
        gfrf = getFilesReleaseFtpEMDB(emdbid="EMD-0070")
        gfrf.set_local_ftp_path("/tmp")  # noqa: S108   Need to check where it is going
        ret = gfrf.get_emdb_volume()
        self.assertIsNone(ret)

    def test_get_header_existing_emdb(self) -> None:
        gfrf = getFilesReleaseFtpEMDB(emdbid="EMD-0070")
        gfrf.set_local_ftp_path("")

        ret = gfrf.get_emdb_xml()
        self.assertIsNotNone(ret)

    def test_get_map_existing_emdb(self) -> None:
        gfrf = getFilesReleaseFtpEMDB(emdbid="EMD-0070")
        gfrf.set_local_ftp_path("")
        ret = gfrf.get_emdb_volume()
        self.assertIsNotNone(ret)

    def test_get_map_non_existing_emdb(self) -> None:
        gfrf = getFilesReleaseFtpEMDB(emdbid="EMD-ABCD", local_ftp_emdb_path="")
        # gfrf.setup_local_temp_ftp(session_path=self.temp_folder)
        ret = gfrf.get_emdb_volume()
        self.assertIsNone(ret)

    def test_get_fsc_existing_emdb(self) -> None:
        gfrf = getFilesReleaseFtpEMDB(emdbid="EMD-10316", local_ftp_emdb_path="")
        # gfrf.setup_local_temp_ftp(session_path=self.temp_folder)
        ret = gfrf.get_emdb_fsc()
        self.assertIsNone(ret)


if __name__ == "__main__":  # pragme: no cover
    unittest.main()
