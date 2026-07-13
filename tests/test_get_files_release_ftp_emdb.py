import shutil
import tempfile
import unittest
import logging

from wwpdb.apps.val_rel.utils.getFilesReleaseFTP_EMDB import getFilesReleaseFtpEMDB

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


class TestsGettingEMDBData(unittest.TestCase):

    def setUp(self):
        self.temp_folder = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_folder, ignore_errors=True)

    def test_checking_header_existing_emdb(self):
        gfrf = getFilesReleaseFtpEMDB(emdbid='EMD-0070')
        # gfrf.setup_local_temp_ftp(session_path=self.temp_folder)
        ret = gfrf.check_header_on_remote_ftp()
        self.assertTrue(ret)

    def test_checking_header_invalid_emdb(self):
        gfrf = getFilesReleaseFtpEMDB(emdbid='EMD-ABCD')
        # gfrf.setup_local_temp_ftp(session_path=self.temp_folder)
        ret = gfrf.check_header_on_remote_ftp()
        self.assertFalse(ret)

    def test_getting_emdb_directory(self):
        gfrf = getFilesReleaseFtpEMDB(emdbid='EMD-0070')
        # gfrf.setup_local_temp_ftp(session_path=self.temp_folder)
        ret = gfrf.get_emdb_from_remote_ftp()
        self.assertTrue(ret)

    def test_getting_emdb_directory_invalid_emdb(self):
        gfrf = getFilesReleaseFtpEMDB(emdbid='EMD-ABCD')
        # gfrf.setup_local_temp_ftp(session_path=self.temp_folder)
        ret = gfrf.get_emdb_from_remote_ftp()
        self.assertFalse(ret)

    def test_get_local_ftp_emdb(self):
        gfrf = getFilesReleaseFtpEMDB(emdbid='EMD-0070')
        gfrf.set_local_ftp_path('')
        ret = gfrf.get_local_ftp_path()
        self.assertEqual(ret, '')

    def test_get_header_empty_local_ftp_emdb(self):
        gfrf = getFilesReleaseFtpEMDB(emdbid='EMD-0070')
        gfrf.set_local_ftp_path('/tmp')
        ret = gfrf.get_emdb_xml()
        print(ret)
        self.assertIsNone(ret)

    def test_get_map_empty_local_ftp_emdb(self):
        gfrf = getFilesReleaseFtpEMDB(emdbid='EMD-0070')
        gfrf.set_local_ftp_path('/tmp')
        ret = gfrf.get_emdb_volume()
        print(ret)
        self.assertIsNone(ret)

    def test_get_header_existing_emdb(self):
        gfrf = getFilesReleaseFtpEMDB(emdbid='EMD-0070')
        gfrf.set_local_ftp_path('')
        print('HERERE')

        ret = gfrf.get_emdb_xml()
        print(ret)
        self.assertIsNotNone(ret)

    def test_get_map_existing_emdb(self):
        gfrf = getFilesReleaseFtpEMDB(emdbid='EMD-0070')
        gfrf.set_local_ftp_path('')
        ret = gfrf.get_emdb_volume()
        print(ret)
        # self.assertIsNotNone(ret)

    def test_get_map_non_existing_emdb(self):
        gfrf = getFilesReleaseFtpEMDB(emdbid='EMD-ABCD', local_ftp_emdb_path='')
        # gfrf.setup_local_temp_ftp(session_path=self.temp_folder)
        ret = gfrf.get_emdb_volume()
        print(ret)
        self.assertIsNone(ret)

    def test_get_fsc_existing_emdb(self):
        gfrf = getFilesReleaseFtpEMDB(emdbid='EMD-10316', local_ftp_emdb_path='')
        # gfrf.setup_local_temp_ftp(session_path=self.temp_folder)
        ret = gfrf.get_emdb_fsc()
        print(ret)
        self.assertIsNone(ret)


if __name__ == '__main__':
    unittest.main()
