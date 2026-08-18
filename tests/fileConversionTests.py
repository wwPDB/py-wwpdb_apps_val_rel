import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

from wwpdb.apps.val_rel.utils.fileConversion import convert_cs_file

MODULE = "wwpdb.apps.val_rel.utils.fileConversion"


class ConvertCsFileTests(unittest.TestCase):
    """Unit tests for convert_cs_file.

    starToPdbx is the actual wwpdb.apps.validation entry point this function
    calls, so it's mocked here -- these tests never run the real star-to-cif
    conversion. DataFile.copy is plain local file I/O (no site config, no
    validation code), so it's exercised for real against temp files.
    """

    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()
        self.working_dir = os.path.join(self.test_dir, "working")
        os.makedirs(self.working_dir)
        self.model_file = os.path.join(self.test_dir, "model.cif")
        with open(self.model_file, "w") as fout:
            fout.write("data_model\n")

        star_to_pdbx_patcher = patch(f"{MODULE}.starToPdbx")
        self.mock_star_to_pdbx = star_to_pdbx_patcher.start()
        self.addCleanup(star_to_pdbx_patcher.stop)
        self.mock_star_to_pdbx.return_value = True

    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _make_cs_file(self, content: str = "data_cs\n") -> str:
        cs_file = os.path.join(self.test_dir, "entry_cs.str")
        with open(cs_file, "w") as fout:
            fout.write(content)
        return cs_file

    def test_missing_cs_file_returns_none(self) -> None:
        missing_cs_file = os.path.join(self.test_dir, "does_not_exist.str")
        ret = convert_cs_file(
            entry_id="1abc", cs_file=missing_cs_file, model_file=self.model_file, working_dir=self.working_dir
        )
        self.assertIsNone(ret)
        self.mock_star_to_pdbx.assert_not_called()

    def test_successful_conversion_returns_cif_path(self) -> None:
        cs_file = self._make_cs_file()
        ret = convert_cs_file(
            entry_id="1abc", cs_file=cs_file, model_file=self.model_file, working_dir=self.working_dir
        )
        expected_cif_path = os.path.join(self.working_dir, "working_cs.cif")
        self.assertEqual(ret, expected_cif_path)

    def test_copies_cs_file_to_working_dir_as_input_cs(self) -> None:
        cs_file = self._make_cs_file(content="data_cs_unique_content\n")
        convert_cs_file(entry_id="1abc", cs_file=cs_file, model_file=self.model_file, working_dir=self.working_dir)
        copied_path = os.path.join(self.working_dir, "input.cs")
        self.assertTrue(os.path.exists(copied_path))
        with open(copied_path) as fin:
            self.assertEqual(fin.read(), "data_cs_unique_content\n")

    def test_calls_star_to_pdbx_with_expected_arguments(self) -> None:
        cs_file = self._make_cs_file()
        convert_cs_file(entry_id="1abc", cs_file=cs_file, model_file=self.model_file, working_dir=self.working_dir)
        self.mock_star_to_pdbx.assert_called_once_with(
            entryId="1abc",
            starPath=os.path.join(self.working_dir, "input.cs"),
            pdbxPath=os.path.join(self.working_dir, "working_cs.cif"),
            modelPath=self.model_file,
            remediation=True,
        )

    def test_failed_conversion_returns_none(self) -> None:
        self.mock_star_to_pdbx.return_value = False
        cs_file = self._make_cs_file()
        ret = convert_cs_file(
            entry_id="1abc", cs_file=cs_file, model_file=self.model_file, working_dir=self.working_dir
        )
        self.assertIsNone(ret)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
