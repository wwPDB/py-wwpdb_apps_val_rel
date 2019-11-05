import unittest
import logging
import os
import tempfile
import shutil
import time
from wwpdb.apps.val_rel.ValidateRelease import already_run

def touch(fname, times=None):
    with open(fname, 'a'):
        os.utime(fname, times)

class ModifiedFolderTests(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.test_input_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.test_input_dir, 'test.file')

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)
        if os.path.exists(self.test_input_dir):
            shutil.rmtree(self.test_input_dir, ignore_errors=True)

    def test_missing_file(self):
        ret = already_run(test_file=self.test_file, output_folder=self.test_dir)
        # expected True - its already run (nothing to do for this file)
        self.assertTrue(ret)

    def test_none_file(self):
        ret = already_run(test_file=None, output_folder=self.test_dir)
        # expected True - its already run (nothing to do for this file)
        self.assertTrue(ret)

    def test_new_file(self):
        touch(self.test_file)
        ret = already_run(test_file=self.test_file, output_folder=self.test_dir)
        # expected False - its not already run
        self.assertFalse(ret)
    
    def test_missing_dir(self):
        touch(self.test_file)
        shutil.rmtree(self.test_dir)
        ret = already_run(test_file=self.test_file, output_folder=self.test_dir)
        # expected False - its not already run
        self.assertFalse(ret)

    def test_new_dir(self):
        touch(self.test_file)
        shutil.rmtree(self.test_dir)
        time.sleep(2)
        os.makedirs(self.test_dir)
        ret = already_run(test_file=self.test_file, output_folder=self.test_dir)
        # expected True - its already run
        self.assertTrue(ret)

if __name__ == '__main__':
    unittest.main()
