import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from wwpdb.apps.val_rel.RemoveExcessOutputFolders import FindExcessEntries

SITE_ID = "WWPDB_DEPLOY_TEST"
MODULE = "wwpdb.apps.val_rel.RemoveExcessOutputFolders"


class BaseRemoveExcessOutputFoldersTest(unittest.TestCase):
    """Common mocking for FindExcessEntries tests.

    getSiteId/outputFiles (site config) and FindAndProcessEntries (which has
    its own dedicated, separately-mocked test coverage and would otherwise
    reach real site config, the network, and validation code) are mocked, so
    these tests only exercise FindExcessEntries's own logic.
    """

    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()

        site_id_patcher = patch(f"{MODULE}.getSiteId")
        self.mock_get_site_id = site_id_patcher.start()
        self.addCleanup(site_id_patcher.stop)
        self.mock_get_site_id.return_value = SITE_ID

        fape_patcher = patch(f"{MODULE}.FindAndProcessEntries")
        self.mock_fape_class = fape_patcher.start()
        self.addCleanup(fape_patcher.stop)
        self.mock_fape = MagicMock()
        self.mock_fape.get_all_pdb_entries.return_value = set()
        self.mock_fape_class.return_value = self.mock_fape

        of_patcher = patch(f"{MODULE}.outputFiles")
        self.mock_of_class = of_patcher.start()
        self.addCleanup(of_patcher.stop)
        self.mock_of = MagicMock()
        self.mock_of.get_pdb_root_folder.return_value = self.test_dir
        self.mock_of.get_emdb_root_folder.return_value = self.test_dir
        self.mock_of_class.return_value = self.mock_of

    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _make_entry_dir(self, name: str) -> str:
        path = os.path.join(self.test_dir, name)
        os.makedirs(path)
        return path


class ConstructorTests(BaseRemoveExcessOutputFoldersTest):
    def test_site_id_defaults_via_get_site_id(self) -> None:
        FindExcessEntries(site_id=None)
        self.mock_get_site_id.assert_called_once()

    def test_site_id_explicit_skips_get_site_id(self) -> None:
        FindExcessEntries(site_id=SITE_ID)
        self.mock_get_site_id.assert_not_called()


class FindPdbAndEmdbEntriesTests(BaseRemoveExcessOutputFoldersTest):
    def test_constructs_fape_with_both_releases_enabled(self) -> None:
        fee = FindExcessEntries(site_id=SITE_ID)
        fee.find_pdb_and_emdb_entries()
        self.mock_fape_class.assert_called_once_with(pdb_release=True, emdb_release=True, site_id=SITE_ID)

    def test_calls_expected_fape_methods(self) -> None:
        fee = FindExcessEntries(site_id=SITE_ID)
        fee.find_pdb_and_emdb_entries()
        self.mock_fape.find_onedep_entries.assert_called_once()
        self.mock_fape.process_emdb_entries.assert_called_once()
        self.mock_fape.process_pdb_entries.assert_called_once()

    def test_stores_all_pdb_entries(self) -> None:
        self.mock_fape.get_all_pdb_entries.return_value = {"1abc", "2xyz"}
        fee = FindExcessEntries(site_id=SITE_ID)
        fee.find_pdb_and_emdb_entries()
        self._make_entry_dir("1abc")
        self._make_entry_dir("3other")
        fee.find_pdb_output_entries()
        fee.check_pdb_entries_output_should_exist()
        # 1abc is a known entry - kept; 3other is not - removed
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "1abc")))
        self.assertFalse(os.path.exists(os.path.join(self.test_dir, "3other")))


class OutputFolderTests(BaseRemoveExcessOutputFoldersTest):
    def test_get_pdb_output_folder_delegates_to_output_files(self) -> None:
        fee = FindExcessEntries(site_id=SITE_ID)
        self.assertEqual(fee.get_pdb_output_folder(), self.test_dir)
        self.mock_of_class.assert_called_with(siteID=SITE_ID)
        self.mock_of.get_pdb_root_folder.assert_called_once()

    def test_get_emdb_output_folder_delegates_to_output_files(self) -> None:
        fee = FindExcessEntries(site_id=SITE_ID)
        self.assertEqual(fee.get_emdb_output_folder(), self.test_dir)
        self.mock_of.get_emdb_root_folder.assert_called_once()


class FindPdbOutputEntriesTests(BaseRemoveExcessOutputFoldersTest):
    def test_lists_entries_in_output_folder(self) -> None:
        self._make_entry_dir("1abc")
        self._make_entry_dir("2xyz")
        fee = FindExcessEntries(site_id=SITE_ID)
        fee.find_pdb_output_entries()
        fee.check_pdb_entries_output_should_exist()
        # Neither is a known entry (default empty set), so both get removed --
        # this incidentally proves find_pdb_output_entries found them both.
        self.assertFalse(os.path.exists(os.path.join(self.test_dir, "1abc")))
        self.assertFalse(os.path.exists(os.path.join(self.test_dir, "2xyz")))

    def test_empty_output_folder_gives_empty_entries(self) -> None:
        fee = FindExcessEntries(site_id=SITE_ID)
        fee.find_pdb_output_entries()
        # No entries to remove, and no error raised.
        fee.check_pdb_entries_output_should_exist()


class CheckPdbEntriesOutputShouldExistTests(BaseRemoveExcessOutputFoldersTest):
    def test_known_entry_is_kept(self) -> None:
        self.mock_fape.get_all_pdb_entries.return_value = {"1abc"}
        self._make_entry_dir("1abc")
        fee = FindExcessEntries(site_id=SITE_ID)
        fee.find_pdb_and_emdb_entries()
        fee.find_pdb_output_entries()
        fee.check_pdb_entries_output_should_exist()
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "1abc")))

    def test_unknown_entry_is_removed(self) -> None:
        self.mock_fape.get_all_pdb_entries.return_value = {"1abc"}
        self._make_entry_dir("2xyz")
        fee = FindExcessEntries(site_id=SITE_ID)
        fee.find_pdb_and_emdb_entries()
        fee.find_pdb_output_entries()
        fee.check_pdb_entries_output_should_exist()
        self.assertFalse(os.path.exists(os.path.join(self.test_dir, "2xyz")))

    def test_dry_run_does_not_remove_unknown_entry(self) -> None:
        self.mock_fape.get_all_pdb_entries.return_value = {"1abc"}
        self._make_entry_dir("2xyz")
        fee = FindExcessEntries(site_id=SITE_ID, dry_run=True)
        fee.find_pdb_and_emdb_entries()
        fee.find_pdb_output_entries()
        fee.check_pdb_entries_output_should_exist()
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "2xyz")))


class RunProcessTests(BaseRemoveExcessOutputFoldersTest):
    def test_run_process_calls_steps_in_order(self) -> None:
        fee = FindExcessEntries(site_id=SITE_ID)
        with patch.object(fee, "find_pdb_and_emdb_entries") as mock_find_ids, patch.object(
            fee, "find_pdb_output_entries"
        ) as mock_find_output, patch.object(fee, "check_pdb_entries_output_should_exist") as mock_check:
            manager = MagicMock()
            manager.attach_mock(mock_find_ids, "find_ids")
            manager.attach_mock(mock_find_output, "find_output")
            manager.attach_mock(mock_check, "check")
            fee.run_process()
        mock_find_ids.assert_called_once()
        mock_find_output.assert_called_once()
        mock_check.assert_called_once()
        self.assertEqual(
            [c[0] for c in manager.mock_calls],
            ["find_ids", "find_output", "check"],
        )

    def test_run_process_end_to_end_removes_unknown_entries(self) -> None:
        self.mock_fape.get_all_pdb_entries.return_value = {"1abc"}
        self._make_entry_dir("1abc")
        self._make_entry_dir("2xyz")
        fee = FindExcessEntries(site_id=SITE_ID)
        fee.run_process()
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "1abc")))
        self.assertFalse(os.path.exists(os.path.join(self.test_dir, "2xyz")))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
