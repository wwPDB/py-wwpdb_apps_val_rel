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

from wwpdb.apps.val_rel.utils.ftp_protocol.getFilesReleaseFTP_PDB import getFilesReleaseFtpPDB


class TestsGettingEMDBData(unittest.TestCase):
    def setUp(self) -> None:
        self.patcher = patch("wwpdb.utils.config.ConfigInfoApp.ConfigInfo", side_effect=FtpStandardConfig)
        self.patcher2 = patch("wwpdb.apps.val_rel.config.ValConfig.ConfigInfo", side_effect=FtpStandardConfig)
        self.patcher.start()
        self.patcher2.start()
        self.temp_folder = tempfile.mkdtemp()
        self.server = "ftp.ebi.ac.uk"
        self.url_prefix = "pub/databases/pdb/data/structures/all/"

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_folder, ignore_errors=True)
        self.patcher.stop()
        self.patcher2.stop()

    def test_checking_model_existing_pdb(self) -> None:
        gfrf = getFilesReleaseFtpPDB(pdbid="1cbs")
        gfrf.setup_local_temp_ftp(session_path=self.temp_folder)
        gfrf.server = self.server
        gfrf.url_prefix = self.url_prefix
        ret = gfrf.get_model()
        self.assertTrue(ret)

    def test_checking_header_invalid_pdb(self) -> None:
        gfrf = getFilesReleaseFtpPDB(pdbid="1cbssFDSDFSF")
        gfrf.setup_local_temp_ftp(session_path=self.temp_folder)
        gfrf.server = self.server
        gfrf.url_prefix = self.url_prefix
        ret = gfrf.get_model()
        self.assertFalse(ret)


if __name__ == "__main__":
    unittest.main()
