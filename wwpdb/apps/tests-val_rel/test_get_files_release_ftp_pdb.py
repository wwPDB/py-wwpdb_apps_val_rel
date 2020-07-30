import shutil
import tempfile
import unittest

from wwpdb.apps.val_rel.utils.getFilesReleaseFTP_PDB import getFilesReleaseFtpPDB


class TestsGettingEMDBData(unittest.TestCase):

    def setUp(self):
        self.temp_folder = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_folder, ignore_errors=True)

    def test_checking_model_existing_pdb(self):
        gfrf = getFilesReleaseFtpPDB(pdbid='1cbs')
        gfrf.setup_local_temp_ftp(session_path=self.temp_folder)
        ret = gfrf.get_model()
        self.assertTrue(ret)

    def test_checking_header_invalid_pdb(self):
        gfrf = getFilesReleaseFtpPDB(pdbid='1cbssFDSDFSF')
        gfrf.setup_local_temp_ftp(session_path=self.temp_folder)
        ret = gfrf.get_model()
        self.assertFalse(ret)


if __name__ == '__main__':
    unittest.main()
