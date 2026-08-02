import unittest
from unittest.mock import MagicMock, patch

from wwpdb.apps.val_rel.utils.find_and_run_missing import FindAndRunMissing

SITE_ID = "WWPDB_DEPLOY_TEST"
MODULE = "wwpdb.apps.val_rel.utils.find_and_run_missing"


class FindAndRunMissingTests(unittest.TestCase):
    """Unit tests for FindAndRunMissing.

    CheckEntries and PopulateValidateRelease are both mocked in full. Between
    them they are what would otherwise reach real site config, ReleasePathInfo,
    and the wwpdb.apps.validation / ValidateRelease pipeline, so mocking them
    here means these tests never touch any of that.
    """

    def setUp(self) -> None:
        ce_patcher = patch(f"{MODULE}.CheckEntries")
        self.mock_ce_class = ce_patcher.start()
        self.addCleanup(ce_patcher.stop)
        self.mock_ce = MagicMock()
        self.mock_ce.read_missing_file.return_value = []
        self.mock_ce_class.return_value = self.mock_ce

        pvr_patcher = patch(f"{MODULE}.PopulateValidateRelease")
        self.mock_pvr_class = pvr_patcher.start()
        self.addCleanup(pvr_patcher.stop)
        self.mock_pvr = MagicMock()
        self.mock_pvr_class.return_value = self.mock_pvr

    def test_constructor_creates_check_entries_with_site_id(self) -> None:
        FindAndRunMissing(siteID=SITE_ID)
        self.mock_ce_class.assert_called_once_with(siteID=SITE_ID)

    def test_find_missing_calls_check_entries_pipeline(self) -> None:
        frm = FindAndRunMissing(siteID=SITE_ID)
        frm.find_missing()
        self.mock_ce.get_entries.assert_called_once_with()
        self.mock_ce.check_entries.assert_called_once_with()
        self.mock_ce.get_failed_entries.assert_called_once_with()

    def test_run_process_read_missing_with_entries_populates_queue(self) -> None:
        self.mock_ce.read_missing_file.return_value = ["1abc", "2xyz"]
        frm = FindAndRunMissing(siteID=SITE_ID, read_missing=True, write_missing=False, priority=True)
        frm.run_process()
        self.mock_ce.read_missing_file.assert_called_once()
        self.mock_pvr_class.assert_called_once_with(
            entry_list=["1abc", "2xyz"],
            validation_sub_dir="missing",
            site_id=SITE_ID,
            always_recalculate=True,
            nocache=True,
            priority=True,
        )
        self.mock_pvr.run_process.assert_called_once()

    def test_run_process_read_missing_no_entries_skips_populate(self) -> None:
        self.mock_ce.read_missing_file.return_value = []
        frm = FindAndRunMissing(siteID=SITE_ID, read_missing=True, write_missing=False)
        frm.run_process()
        self.mock_ce.read_missing_file.assert_called_once()
        self.mock_pvr_class.assert_not_called()

    def test_run_process_write_missing_calls_find_missing_and_writes(self) -> None:
        frm = FindAndRunMissing(siteID=SITE_ID, read_missing=False, write_missing=True)
        frm.run_process()
        self.mock_ce.get_entries.assert_called_once()
        self.mock_ce.check_entries.assert_called_once()
        self.mock_ce.write_missing_file.assert_called_once()
        self.mock_pvr_class.assert_not_called()

    def test_run_process_neither_flag_does_nothing(self) -> None:
        frm = FindAndRunMissing(siteID=SITE_ID, read_missing=False, write_missing=False)
        frm.run_process()
        self.mock_ce.read_missing_file.assert_not_called()
        self.mock_ce.get_entries.assert_not_called()
        self.mock_ce.write_missing_file.assert_not_called()
        self.mock_pvr_class.assert_not_called()

    def test_run_process_both_flags_does_both(self) -> None:
        self.mock_ce.read_missing_file.return_value = ["1abc"]
        frm = FindAndRunMissing(siteID=SITE_ID, read_missing=True, write_missing=True)
        frm.run_process()
        self.mock_pvr_class.assert_called_once()
        self.mock_ce.get_entries.assert_called_once()
        self.mock_ce.write_missing_file.assert_called_once()

    def test_run_process_default_flags_only_reads(self) -> None:
        # Defaults: write_missing=False, read_missing=True
        frm = FindAndRunMissing(siteID=SITE_ID)
        frm.run_process()
        self.mock_ce.read_missing_file.assert_called_once()
        self.mock_ce.get_entries.assert_not_called()
        self.mock_ce.write_missing_file.assert_not_called()

    def test_priority_false_propagates_to_populate_queue(self) -> None:
        self.mock_ce.read_missing_file.return_value = ["1abc"]
        frm = FindAndRunMissing(siteID=SITE_ID, priority=False)
        frm.run_process()
        self.assertFalse(self.mock_pvr_class.call_args.kwargs["priority"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
