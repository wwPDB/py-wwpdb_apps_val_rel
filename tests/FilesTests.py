import os
import shutil
import tempfile
import unittest
from typing import Optional, Tuple, Union

from wwpdb.apps.val_rel.utils.Files import copy_file, get_gzip_name, gzip_file, remove_files


def touch(fname: str, times: Optional[Tuple[Union[int, float], Union[int, float]]] = None) -> None:
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

    def test_gzip_none_file(self) -> None:
        ret = gzip_file(None, self.output_dir)
        self.assertFalse(ret)

    def test_gzip_file_no_output_folder(self) -> None:
        input_folder = tempfile.mkdtemp()
        input_file = os.path.join(input_folder, "test.file")
        touch(input_file)
        ret = gzip_file(input_file, None)
        self.assertFalse(ret)
        shutil.rmtree(input_folder)

    def test_copy_file_no_output_folder(self) -> None:
        input_folder = tempfile.mkdtemp()
        input_file = os.path.join(input_folder, "test.file")
        touch(input_file)
        ret = copy_file(input_file, None)
        self.assertFalse(ret)
        shutil.rmtree(input_folder)

    def test_copy_file_creates_missing_output_folder(self) -> None:
        input_folder = tempfile.mkdtemp()
        input_file = os.path.join(input_folder, "test.file")
        touch(input_file)
        missing_output_dir = os.path.join(self.output_dir, "does_not_exist_yet")
        expected_file = os.path.join(missing_output_dir, "test.file")
        ret = copy_file(input_file, missing_output_dir)
        self.assertTrue(ret)
        self.assertTrue(os.path.exists(expected_file))
        shutil.rmtree(input_folder)

    def test_remove_files_removes_existing(self) -> None:
        file1 = os.path.join(self.output_dir, "one.file")
        file2 = os.path.join(self.output_dir, "two.file")
        touch(file1)
        touch(file2)
        remove_files([file1, file2])
        self.assertFalse(os.path.exists(file1))
        self.assertFalse(os.path.exists(file2))

    def test_remove_files_removes_gzip_variant(self) -> None:
        gzfile = os.path.join(self.output_dir, "three.file.gz")
        touch(gzfile)
        # The base (non-gz) file is not present - only the .gz variant is removed
        remove_files([os.path.join(self.output_dir, "three.file")])
        self.assertFalse(os.path.exists(gzfile))

    def test_remove_files_none_list(self) -> None:
        remove_files(None)

    def test_remove_files_empty_list(self) -> None:
        remove_files([])

    def test_remove_files_missing_file_no_error(self) -> None:
        remove_files([os.path.join(self.output_dir, "does_not_exist.file")])

    def test_remove_files_with_falsy_entry(self) -> None:
        file1 = os.path.join(self.output_dir, "one.file")
        touch(file1)
        remove_files([file1, "", None])  # type: ignore[list-item]
        self.assertFalse(os.path.exists(file1))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
