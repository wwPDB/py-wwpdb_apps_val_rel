import unittest
import os
import shutil
import tempfile

from wwpdb.apps.val_rel.utils.getRemoteFilesHTTP import GetRemoteFiles

class TestRemoteFilesHTTP(unittest.TestCase):

    def setUp(self):
        self.output_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.output_dir, ignore_errors=True)

    def test_get_emdb_header(self):
        grf = GetRemoteFiles(output_path=self.output_dir)
        grf.get_url(url='http://ftp.ebi.ac.uk/pub/databases/emdb/structures/EMD-0070/header/emd-0070-v30.xml')
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, 'emd-0070-v30.xml')))

    def test_get_emdb_folder(self):
        grf = GetRemoteFiles(output_path=self.output_dir)
        grf.get_url(url='http://ftp.ebi.ac.uk/pub/databases/emdb/structures/EMD-0070')
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, 'header', 'emd-0070-v30.xml')))

if __name__ == '__main__':
    unittest.main()
