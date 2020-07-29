import glob
import os
import shutil
import tempfile
import unittest

from wwpdb.apps.val_rel.utils.getRemoteFilesFTP import GetRemoteFiles


class TestRemoteFiles(unittest.TestCase):

    def setUp(self):
        self.output_dir = tempfile.mkdtemp()
        self.gfr = GetRemoteFiles(output_path=self.output_dir, server='ftp.ebi.ac.uk')

    def tearDown(self):
        shutil.rmtree(self.output_dir, ignore_errors=True)

    def test_emdb_header(self):
        ret = self.gfr.get_url(
            directory='pub/databases/emdb/structures/EMD-0070/header',
            filename='emd-0070-v30.xml')
        self.assertEqual(len(ret), 1)
        expected_file = os.path.join(self.output_dir, ret[0])
        self.assertTrue(os.path.exists(expected_file))

    def test_emdb_folder(self):
        self.gfr.get_directory(directory='pub/databases/emdb/structures/EMD-0070/header')
        ret = glob.glob(os.path.join(self.output_dir, '*'))
        self.assertEqual(len(ret), 3)
        for f in ret:
            expected_file = os.path.join(self.output_dir, f)
            self.assertTrue(os.path.exists(expected_file))

    def test_emdb_sub_folders(self):
        self.gfr.get_directory(
            directory='pub/databases/emdb/structures/EMD-0070',
        )
        ret = glob.glob(os.path.join(self.output_dir, '*'))
        self.assertEqual(len(ret), 3)


if __name__ == '__main__':
    unittest.main()
