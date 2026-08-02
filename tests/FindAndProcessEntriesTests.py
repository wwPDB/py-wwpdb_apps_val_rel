import os
import shutil
import tempfile
import unittest
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, patch

from wwpdb.apps.val_rel.utils.FindAndProcessEntries import FindAndProcessEntries

SITE_ID = "WWPDB_DEPLOY_TEST"
MODULE = "wwpdb.apps.val_rel.utils.FindAndProcessEntries"


class FindAndProcessEntriesTests(unittest.TestCase):
    """Unit tests for FindAndProcessEntries.

    Site config (getSiteId/outputFiles) and every network-touching collaborator
    (getFilesRelease, which is what would eventually reach GetRemoteFilesHttp and
    EmailHandler on a real system) are mocked, so these tests never contact real
    site configuration, the network, or send an email.
    """

    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()

        site_id_patcher = patch(f"{MODULE}.getSiteId")
        self.mock_get_site_id = site_id_patcher.start()
        self.addCleanup(site_id_patcher.stop)
        self.mock_get_site_id.return_value = SITE_ID

        of_patcher = patch(f"{MODULE}.outputFiles")
        mock_of_class = of_patcher.start()
        self.addCleanup(of_patcher.stop)
        self.mock_of = MagicMock()
        self.mock_of.get_ftp_cache_folder.return_value = "/cache/folder"
        mock_of_class.return_value = self.mock_of

        fe_patcher = patch(f"{MODULE}.FindEntries")
        mock_fe_class = fe_patcher.start()
        self.addCleanup(fe_patcher.stop)
        self.mock_fe = MagicMock()
        self.mock_fe.get_added_pdb_entries.return_value = []
        self.mock_fe.get_modified_pdb_entries.return_value = []
        self.mock_fe.get_emdb_entries.return_value = []
        mock_fe_class.return_value = self.mock_fe

        gfr_patcher = patch(f"{MODULE}.getFilesRelease")
        self.mock_gfr_class = gfr_patcher.start()
        self.addCleanup(gfr_patcher.stop)

        xml_patcher = patch(f"{MODULE}.XmlInfo")
        self.mock_xmlinfo_class = xml_patcher.start()
        self.addCleanup(xml_patcher.stop)

        mmcif_patcher = patch(f"{MODULE}.mmCIFInfo")
        self.mock_mmcifinfo_class = mmcif_patcher.start()
        self.addCleanup(mmcif_patcher.stop)

    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _make(self, **kwargs: Any) -> FindAndProcessEntries:
        kwargs.setdefault("site_id", SITE_ID)
        return FindAndProcessEntries(**kwargs)

    # -- constructor -----------------------------------------------------

    def test_site_id_defaults_via_get_site_id(self) -> None:
        FindAndProcessEntries(site_id=None)
        self.mock_get_site_id.assert_called_once()

    def test_site_id_explicit_skips_get_site_id(self) -> None:
        self._make()
        self.mock_get_site_id.assert_not_called()

    def test_nocache_true_passes_none_cache_to_getFilesRelease(self) -> None:
        self._mock_gfr()
        fape = self._make(nocache=True, entry_list=["EMD-1234"])
        fape.process_entry_list()
        fape.categorise_entries()
        fape.process_emdb_entries()
        self.assertIsNone(self.mock_gfr_class.call_args.kwargs["cache"])

    def test_nocache_false_passes_ftp_cache_folder_to_getFilesRelease(self) -> None:
        self._mock_gfr()
        fape = self._make(nocache=False, entry_list=["EMD-1234"])
        fape.process_entry_list()
        fape.categorise_entries()
        fape.process_emdb_entries()
        self.assertEqual(self.mock_gfr_class.call_args.kwargs["cache"], "/cache/folder")

    def test_default_entry_list_is_empty(self) -> None:
        fape = self._make()
        self.assertEqual(fape.get_pdb_entries(), [])

    # -- find_onedep_entries ----------------------------------------------

    def test_find_onedep_entries_pdb_release(self) -> None:
        self.mock_fe.get_added_pdb_entries.return_value = ["1abc"]
        self.mock_fe.get_modified_pdb_entries.return_value = ["2xyz"]
        fape = self._make(pdb_release=True)
        fape.find_onedep_entries()
        self.assertEqual(sorted(fape.get_pdb_entries()), ["1abc", "2xyz"])
        self.assertEqual(fape.get_all_pdb_entries(), {"1abc", "2xyz"})

    def test_find_onedep_entries_emdb_release(self) -> None:
        self.mock_fe.get_emdb_entries.return_value = ["EMD-1234"]
        fape = self._make(emdb_release=True)
        fape.find_onedep_entries()
        self.assertEqual(fape.get_emdb_entries(), ["EMD-1234"])

    def test_find_onedep_entries_neither_release(self) -> None:
        self.mock_fe.get_added_pdb_entries.return_value = ["1abc"]
        self.mock_fe.get_emdb_entries.return_value = ["EMD-1234"]
        fape = self._make(pdb_release=False, emdb_release=False)
        fape.find_onedep_entries()
        self.assertEqual(fape.get_pdb_entries(), [])
        self.assertEqual(fape.get_emdb_entries(), [])

    # -- process_entry_file ------------------------------------------------

    def test_process_entry_file_reads_stripped_lines(self) -> None:
        entry_file = os.path.join(self.test_dir, "entries.txt")
        with open(entry_file, "w") as fout:
            fout.write("1abc\n2xyz\n")
        fape = self._make(entry_file=entry_file)
        fape.process_entry_file()
        fape.categorise_entries()
        self.assertEqual(sorted(fape.get_pdb_entries()), ["1abc", "2xyz"])

    def test_process_entry_file_missing_file_logs_error_no_entries(self) -> None:
        fape = self._make(entry_file=os.path.join(self.test_dir, "does_not_exist.txt"))
        fape.process_entry_file()
        fape.categorise_entries()
        self.assertEqual(fape.get_pdb_entries(), [])

    def test_process_entry_file_empty_string_is_noop(self) -> None:
        fape = self._make(entry_file="")
        fape.process_entry_file()
        fape.categorise_entries()
        self.assertEqual(fape.get_pdb_entries(), [])

    # -- process_entry_list / process_entry_string -------------------------

    def test_process_entry_list(self) -> None:
        fape = self._make(entry_list=["1abc", "EMD-1234"])
        fape.process_entry_list()
        fape.categorise_entries()
        self.assertEqual(fape.get_pdb_entries(), ["1abc"])
        self.assertEqual(fape.get_emdb_entries(), ["EMD-1234"])

    def test_process_entry_string(self) -> None:
        fape = self._make(entry_string="1abc,EMD-1234,2xyz")
        fape.process_entry_string()
        fape.categorise_entries()
        self.assertEqual(sorted(fape.get_pdb_entries()), ["1abc", "2xyz"])
        self.assertEqual(fape.get_emdb_entries(), ["EMD-1234"])

    def test_categorise_entries_case_insensitive(self) -> None:
        fape = self._make(entry_string="emd-1234")
        fape.process_entry_string()
        fape.categorise_entries()
        self.assertEqual(fape.get_emdb_entries(), ["emd-1234"])
        self.assertEqual(fape.get_pdb_entries(), [])

    # -- process_pdb_entries ------------------------------------------------

    def test_process_pdb_entries_adds_message_once(self) -> None:
        fape = self._make(entry_list=["1abc"])
        fape.process_entry_list()
        fape.categorise_entries()
        fape.process_pdb_entries()
        self.assertEqual(fape.get_found_entries(), [{"pdbID": "1abc"}])
        self.assertEqual(fape.get_added_entries(), ["1abc"])

    def test_process_pdb_entries_skips_already_added(self) -> None:
        fape = self._make(entry_list=["1abc"])
        fape.process_entry_list()
        fape.categorise_entries()
        fape.add_entry("1abc")
        fape.process_pdb_entries()
        self.assertEqual(fape.get_found_entries(), [])

    # -- process_emdb_entries -------------------------------------------------

    def _mock_gfr(
        self,
        emdb_xml: Optional[str] = "emd-1234.xml",
        emdb_volume: Optional[str] = "emd-1234.map",
        model: Optional[str] = "1abc.cif",
    ) -> MagicMock:
        mock_gfr = MagicMock()
        mock_gfr.get_emdb_xml.return_value = emdb_xml
        mock_gfr.get_emdb_volume.return_value = emdb_volume
        mock_gfr.get_model.return_value = model
        self.mock_gfr_class.return_value = mock_gfr
        return mock_gfr

    def test_process_emdb_entries_adds_message_and_removes_temp_files(self) -> None:
        mock_gfr = self._mock_gfr()
        self.mock_xmlinfo_class.return_value.get_pdbids_from_xml.return_value = []
        fape = self._make(entry_list=["EMD-1234"])
        fape.process_entry_list()
        fape.categorise_entries()
        fape.process_emdb_entries()
        self.assertEqual(fape.get_found_entries(), [{"emdbID": "EMD-1234"}])
        self.assertEqual(fape.get_added_entries(), ["EMD-1234"])
        mock_gfr.remove_local_temp_files.assert_called_once()

    def test_process_emdb_entries_skips_already_added(self) -> None:
        fape = self._make(entry_list=["EMD-1234"])
        fape.process_entry_list()
        fape.categorise_entries()
        fape.add_entry("EMD-1234")
        fape.process_emdb_entries()
        self.assertEqual(fape.get_found_entries(), [])
        self.mock_gfr_class.assert_not_called()

    def test_process_emdb_entries_no_volume_skips_entry(self) -> None:
        self._mock_gfr(emdb_volume=None)
        fape = self._make(entry_list=["EMD-1234"])
        fape.process_entry_list()
        fape.categorise_entries()
        fape.process_emdb_entries()
        self.assertEqual(fape.get_found_entries(), [])
        self.assertEqual(fape.get_added_entries(), [])

    def test_process_emdb_entries_no_xml_skips_entry(self) -> None:
        self._mock_gfr(emdb_xml=None)
        fape = self._make(entry_list=["EMD-1234"])
        fape.process_entry_list()
        fape.categorise_entries()
        fape.process_emdb_entries()
        self.assertEqual(fape.get_found_entries(), [])
        self.assertEqual(fape.get_added_entries(), [])

    def test_process_emdb_entries_removes_matching_pdb_from_queue(self) -> None:
        self._mock_gfr()
        self.mock_xmlinfo_class.return_value.get_pdbids_from_xml.return_value = ["1ABC"]
        self.mock_mmcifinfo_class.return_value.get_associated_emdb.return_value = "EMD-1234"
        fape = self._make(entry_string="1abc,EMD-1234")
        fape.process_entry_string()
        fape.categorise_entries()
        fape.process_emdb_entries()
        self.assertNotIn("1abc", fape.get_pdb_entries())

    def test_process_emdb_entries_adds_new_matching_pdb_to_all_entries(self) -> None:
        self._mock_gfr()
        self.mock_xmlinfo_class.return_value.get_pdbids_from_xml.return_value = ["1ABC"]
        self.mock_mmcifinfo_class.return_value.get_associated_emdb.return_value = "EMD-1234"
        fape = self._make(entry_list=["EMD-1234"])
        fape.process_entry_list()
        fape.categorise_entries()
        fape.process_emdb_entries()
        self.assertIn("1abc", fape.get_all_pdb_entries())

    def test_process_emdb_entries_removes_pdb_when_model_missing(self) -> None:
        self._mock_gfr(model=None)
        self.mock_xmlinfo_class.return_value.get_pdbids_from_xml.return_value = ["1ABC"]
        fape = self._make(entry_string="1abc,EMD-1234")
        fape.process_entry_string()
        fape.categorise_entries()
        fape.process_emdb_entries()
        self.assertNotIn("1abc", fape.get_pdb_entries())

    def test_process_emdb_entries_exception_is_caught(self) -> None:
        self.mock_gfr_class.side_effect = RuntimeError("boom")
        fape = self._make(entry_list=["EMD-1234"])
        fape.process_entry_list()
        fape.categorise_entries()
        fape.process_emdb_entries()  # should not raise
        self.assertEqual(fape.get_found_entries(), [])

    # -- misc getters / mutators --------------------------------------------

    def test_add_message(self) -> None:
        fape = self._make()
        message: Dict[str, Any] = {"pdbID": "1abc"}
        fape.add_message(message)
        self.assertEqual(fape.get_found_entries(), [message])

    def test_add_entry(self) -> None:
        fape = self._make()
        fape.add_entry("1abc")
        self.assertEqual(fape.get_added_entries(), ["1abc"])

    # -- orchestration -------------------------------------------------------

    def test_run_process_delegates_to_find_and_process_entries(self) -> None:
        fape = self._make()
        with patch.object(fape, "find_and_process_entries") as mock_fape:
            fape.run_process()
            mock_fape.assert_called_once()

    def test_find_and_process_entries_end_to_end_pdb_only(self) -> None:
        fape = self._make(entry_list=["1abc"])
        fape.find_and_process_entries()
        self.assertEqual(fape.get_found_entries(), [{"pdbID": "1abc"}])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
