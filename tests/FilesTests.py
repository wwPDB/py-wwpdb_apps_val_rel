import os
import shutil
import tempfile
import unittest
from typing import Optional, Tuple, Union

from wwpdb.apps.val_rel.utils.Files import copy_file, get_gzip_name, gzip_file


def touch(fname, times: Optional[Tuple[Union[int, float], Union[int, float]]] = None):
    with open(fname, "a"):
        os.utime(fname, times)


class TestFiles(unittest.TestCase):
    def setUp(self) -> None:
        self.output_dir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        shutil.rmtree(self.output_dir)

    def test_get_gzip_name(self) -> None:
        fname = "my.file"
        expected_name = "my.file.gz"
        ret = get_gzip_name(fname)
        self.assertEqual(expected_name, ret)

    def test_get_gzip_name_none(self) -> None:
        fname = None
        ret = get_gzip_name(fname)
        self.assertIsNone(ret)

    def test_get_gzip_name_empty(self) -> None:
        fname = ""
        ret = get_gzip_name(fname)
        self.assertIsNone(ret)

    def test_gzip_file(self) -> None:
        input_folder = tempfile.mkdtemp()
        input_file = os.path.join(input_folder, "test.file")
        touch(input_file)
        expected_file = os.path.join(self.output_dir, input_file + ".gz")
        ret = gzip_file(input_file, self.output_dir)
        self.assertTrue(ret)
        self.assertTrue(os.path.exists(expected_file))
        shutil.rmtree(input_folder)

    def test_copy_file(self) -> None:
        input_folder = tempfile.mkdtemp()
        input_file = os.path.join(input_folder, "test.file")
        touch(input_file)
        expected_file = os.path.join(self.output_dir, input_file)
        ret = copy_file(input_file, self.output_dir)
        self.assertTrue(ret)
        self.assertTrue(os.path.exists(expected_file))
        shutil.rmtree(input_folder)

    def test_gzip_missing_file(self) -> None:
        input_file = "missing_file"
        expected_output = os.path.join(self.output_dir, input_file + ".gz")
        ret = gzip_file(input_file, self.output_dir)
        self.assertFalse(ret)
        self.assertFalse(os.path.exists(expected_output))

    def test_copy_missing_file(self) -> None:
        input_file = "missing_file"
        expected_output = os.path.join(self.output_dir, input_file)
        ret = copy_file(input_file, self.output_dir)
        self.assertFalse(ret)
        self.assertFalse(os.path.exists(expected_output))

    def test_copy_none_file(self) -> None:
        input_file = None
        ret = copy_file(input_file, self.output_dir)
        self.assertFalse(ret)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
