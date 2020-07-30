import shutil
import tempfile
import unittest

from wwpdb.apps.val_rel.utils.getFilesReleaseFTP_EMDB import getFilesReleaseFtpEMDB


class TestsGettingEMDBData(unittest.TestCase):

    def setUp(self):
        self.temp_folder = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_folder, ignore_errors=True)

    def test_checking_header_existing_emdb(self):
        gfrf = getFilesReleaseFtpEMDB(emdbid='EMD-0070')
        gfrf.setup_local_temp_ftp(session_path=self.temp_folder)
        ret = gfrf.check_header_on_remote_ftp()
        self.assertTrue(ret)

    def test_checking_header_invalid_emdb(self):
        gfrf = getFilesReleaseFtpEMDB(emdbid='EMD-ABCD')
        gfrf.setup_local_temp_ftp(session_path=self.temp_folder)
        ret = gfrf.check_header_on_remote_ftp()
        self.assertFalse(ret)

    def test_getting_emdb_directory(self):
        gfrf = getFilesReleaseFtpEMDB(emdbid='EMD-0070')
        gfrf.setup_local_temp_ftp(session_path=self.temp_folder)
        ret = gfrf.get_emdb_from_remote_ftp()
        self.assertTrue(ret)

    def test_getting_emdb_directory_invalid_emdb(self):
        gfrf = getFilesReleaseFtpEMDB(emdbid='EMD-ABCD')
        gfrf.setup_local_temp_ftp(session_path=self.temp_folder)
        ret = gfrf.get_emdb_from_remote_ftp()
        self.assertFalse(ret)

    def test_get_header_existing_emdb(self):
        gfrf = getFilesReleaseFtpEMDB(emdbid='EMD-0070', local_ftp_emdb_path='/tmp')
        gfrf.setup_local_temp_ftp(session_path=self.temp_folder)
        ret = gfrf.get_emdb_xml()
        print(ret)
        self.assertIsNotNone(ret)

    def test_get_map_existing_emdb(self):
        gfrf = getFilesReleaseFtpEMDB(emdbid='EMD-0070', local_ftp_emdb_path='/tmp')
        gfrf.setup_local_temp_ftp(session_path=self.temp_folder)
        ret = gfrf.get_emdb_volume()
        print(ret)
        self.assertIsNotNone(ret)

    def test_get_map_non_existing_emdb(self):
        gfrf = getFilesReleaseFtpEMDB(emdbid='EMD-ABCD', local_ftp_emdb_path='/tmp')
        gfrf.setup_local_temp_ftp(session_path=self.temp_folder)
        ret = gfrf.get_emdb_volume()
        print(ret)
        self.assertIsNone(ret)


if __name__ == '__main__':
    unittest.main()