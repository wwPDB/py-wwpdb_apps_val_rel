import os
import shutil
import tempfile
import unittest
from typing import Dict, Sequence
from unittest.mock import MagicMock, patch

from wwpdb.apps.val_rel.utils.FindEntries import FindEntries

SITE_ID = "WWPDB_DEPLOY_TEST"


class FindEntriesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()
        self.added_path = os.path.join(self.test_dir, "added")
        self.modified_path = os.path.join(self.test_dir, "modified")
        self.emd_path = os.path.join(self.test_dir, "emd")
        self.paths: Dict[str, str] = {
            "added": self.added_path,
            "modified": self.modified_path,
            "emd": self.emd_path,
        }

        rpi_patcher = patch("wwpdb.apps.val_rel.utils.FindEntries.ReleasePathInfo")
        mock_rpi_class = rpi_patcher.start()
        self.addCleanup(rpi_patcher.stop)
        self.mock_rpi = MagicMock()
        mock_rpi_class.return_value = self.mock_rpi
        self.mock_rpi.getForReleasePath.side_effect = lambda subdir: self.paths[subdir]

        site_id_patcher = patch("wwpdb.apps.val_rel.utils.FindEntries.getSiteId")
        self.mock_get_site_id = site_id_patcher.start()
        self.addCleanup(site_id_patcher.stop)
        self.mock_get_site_id.return_value = SITE_ID

    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _populate(
        self, subfolder: str, dirs: Sequence[str] = (), new_dirs: Sequence[str] = (), files: Sequence[str] = ()
    ) -> None:
        base = self.paths[subfolder]
        os.makedirs(base, exist_ok=True)
        for d in dirs:
            os.makedirs(os.path.join(base, d))
        for d in new_dirs:
            os.makedirs(os.path.join(base, d))
        for f in files:
            with open(os.path.join(base, f), "w") as fout:
                fout.write("data")

    def test_site_id_defaults_via_get_site_id(self) -> None:
        FindEntries(siteID=None)
        self.mock_get_site_id.assert_called_once()

    def test_site_id_explicit_skips_get_site_id(self) -> None:
        FindEntries(siteID=SITE_ID)
        self.mock_get_site_id.assert_not_called()

    def test_get_added_pdb_entries(self) -> None:
        self._populate("added", dirs=["1abc", "1xyz"], new_dirs=["2new.new"], files=["stray.txt"])
        fe = FindEntries(siteID=SITE_ID)
        self.assertEqual(sorted(fe.get_added_pdb_entries()), ["1abc", "1xyz"])

    def test_get_modified_pdb_entries(self) -> None:
        self._populate("modified", dirs=["1abc"], new_dirs=["1xyz.new"])
        fe = FindEntries(siteID=SITE_ID)
        self.assertEqual(fe.get_modified_pdb_entries(), ["1abc"])

    def test_get_emdb_entries(self) -> None:
        self._populate("emd", dirs=["EMD-1234", "EMD-5678"])
        fe = FindEntries(siteID=SITE_ID)
        self.assertEqual(sorted(fe.get_emdb_entries()), ["EMD-1234", "EMD-5678"])

    def test_get_added_pdb_paths(self) -> None:
        self._populate("added", dirs=["1abc"])
        fe = FindEntries(siteID=SITE_ID)
        self.assertEqual(fe.get_added_pdb_paths(), [os.path.join(self.added_path, "1abc")])

    def test_get_modified_pdb_paths(self) -> None:
        self._populate("modified", dirs=["1abc"])
        fe = FindEntries(siteID=SITE_ID)
        self.assertEqual(fe.get_modified_pdb_paths(), [os.path.join(self.modified_path, "1abc")])

    def test_get_emdb_paths(self) -> None:
        self._populate("emd", dirs=["EMD-1234"])
        fe = FindEntries(siteID=SITE_ID)
        self.assertEqual(fe.get_emdb_paths(), [os.path.join(self.emd_path, "EMD-1234")])

    def test_empty_directory_returns_empty_list(self) -> None:
        os.makedirs(self.added_path)
        fe = FindEntries(siteID=SITE_ID)
        self.assertEqual(fe.get_added_pdb_entries(), [])
        self.assertEqual(fe.get_added_pdb_paths(), [])

    def test_new_directories_are_excluded(self) -> None:
        self._populate("added", new_dirs=["1abc.new"])
        fe = FindEntries(siteID=SITE_ID)
        self.assertEqual(fe.get_added_pdb_entries(), [])
        self.assertEqual(fe.get_added_pdb_paths(), [])

    def test_files_are_excluded(self) -> None:
        self._populate("added", files=["notes.txt"])
        fe = FindEntries(siteID=SITE_ID)
        self.assertEqual(fe.get_added_pdb_entries(), [])
        self.assertEqual(fe.get_added_pdb_paths(), [])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
