import os
import shutil
import tempfile
import unittest
import time

from wwpdb.apps.val_rel.utils.checkModifications import already_run


def touch(fname, times=None):
    with open(fname, "a"):
        os.utime(fname, times)


class TestModification(unittest.TestCase):

    def setUp(self):
        self.input_folder = tempfile.mkdtemp()
        self.input_file = os.path.join(self.input_folder, 'test.file')
        touch(self.input_file)
        time.sleep(1)
        self.output_folder = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.output_folder):
            shutil.rmtree(self.output_folder)
        if os.path.exists(self.input_folder):
            shutil.rmtree(self.input_folder, ignore_errors=True)

    def test_newer_file(self):
        touch(self.input_file)
        ret = already_run(test_file=self.input_file,
                          output_folder=self.output_folder
                          )
        self.assertFalse(ret)

    def test_older_file(self):
        ret = already_run(test_file=self.input_file,
                          output_folder=self.output_folder
                          )
        self.assertTrue(ret)

    def test_missing_file(self):
        os.remove(self.input_file)
        ret = already_run(test_file=self.input_file,
                          output_folder=self.output_folder
                          )
        self.assertTrue(ret)

    def test_missing_folder(self):
        shutil.rmtree(self.output_folder)
        ret = already_run(test_file=self.input_file,
                          output_folder=self.output_folder
                          )
        self.assertFalse(ret)


if __name__ == '__main__':
    unittest.main()
