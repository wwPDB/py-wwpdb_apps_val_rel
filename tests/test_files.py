import os
import shutil
import tempfile
import unittest

from wwpdb.apps.val_rel.utils.Files import get_gzip_name, gzip_file, copy_file


def touch(fname, times=None):
    with open(fname, "a"):
        os.utime(fname, times)


class TestFiles(unittest.TestCase):

    def setUp(self):
        self.output_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.output_dir)

    def test_get_gzip_name(self):
        fname = 'my.file'
        expected_name = 'my.file.gz'
        ret = get_gzip_name(fname)
        self.assertEqual(expected_name, ret)

    def test_get_gzip_name_none(self):
        fname = None
        ret = get_gzip_name(fname)
        self.assertIsNone(ret)

    def test_get_gzip_name_empty(self):
        fname = ''
        ret = get_gzip_name(fname)
        self.assertIsNone(ret)

    def test_gzip_file(self):
        input_folder = tempfile.mkdtemp()
        input_file = os.path.join(input_folder, 'test.file')
        touch(input_file)
        expected_file = os.path.join(self.output_dir, input_file + '.gz')
        ret = gzip_file(input_file, self.output_dir)
        self.assertTrue(ret)
        self.assertTrue(os.path.exists(expected_file))
        shutil.rmtree(input_folder)

    def test_copy_file(self):
        input_folder = tempfile.mkdtemp()
        input_file = os.path.join(input_folder, 'test.file')
        touch(input_file)
        expected_file = os.path.join(self.output_dir, input_file)
        ret = copy_file(input_file, self.output_dir)
        self.assertTrue(ret)
        self.assertTrue(os.path.exists(expected_file))
        shutil.rmtree(input_folder)

    def test_gzip_missing_file(self):
        input_file = 'missing_file'
        expected_output = os.path.join(self.output_dir, input_file + '.gz')
        ret = gzip_file(input_file, self.output_dir)
        self.assertFalse(ret)
        self.assertFalse(os.path.exists(expected_output))

    def test_copy_missing_file(self):
        input_file = 'missing_file'
        expected_output = os.path.join(self.output_dir, input_file)
        ret = copy_file(input_file, self.output_dir)
        self.assertFalse(ret)
        self.assertFalse(os.path.exists(expected_output))

    def test_copy_none_file(self):
        input_file = None
        ret = copy_file(input_file, self.output_dir)
        self.assertFalse(ret)


if __name__ == '__main__':
    unittest.main()
