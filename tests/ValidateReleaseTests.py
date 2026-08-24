import os
import shutil
import sys
import tempfile
import unittest
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, patch

from wwpdb.apps.val_rel.ValidateRelease import runValidation

SITE_ID = "WWPDB_DEPLOY_TEST"
MODULE = "wwpdb.apps.val_rel.ValidateRelease"


def _configure_output_files_mock(mock_of: MagicMock, tmp_dir: str) -> None:
    mock_of.get_entry_output_folder.return_value = os.path.join(tmp_dir, "output")
    mock_of.get_pdb_validation_images_output_folder.return_value = os.path.join(tmp_dir, "images")
    mock_of.get_core_validation_files.return_value = {"pdf": os.path.join(tmp_dir, "output", "entry.pdf")}
    mock_of.get_validation_files_for_separate_location.return_value = {
        "image_tar": os.path.join(tmp_dir, "images", "entry_images.tar")
    }
    mock_of.get_validation_xml.return_value = os.path.join(tmp_dir, "output", "entry.xml")
    mock_of.get_all_validation_files.return_value = {"pdf": os.path.join(tmp_dir, "output", "entry.pdf")}
    mock_of.get_pdb_output_folder.return_value = os.path.join(tmp_dir, "pdb_output")
    mock_of.get_emdb_output_folder.return_value = os.path.join(tmp_dir, "emdb_output")
    mock_of.get_root_state_folder.return_value = os.path.join(tmp_dir, "state")
    mock_of.get_ftp_cache_folder.return_value = os.path.join(tmp_dir, "cache")


class BaseValidateReleaseTest(unittest.TestCase):
    """Common mocking for runValidation tests.

    getSiteId/ValConfig (site config) and getFilesRelease/outputFiles/ValDataStore
    (the collaborators that would otherwise reach real site config, the network,
    and wwpdb.apps.validation) are mocked here so subclasses never touch any of
    that by default.
    """

    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()

        site_id_patcher = patch(f"{MODULE}.getSiteId")
        self.mock_get_site_id = site_id_patcher.start()
        self.addCleanup(site_id_patcher.stop)
        self.mock_get_site_id.return_value = SITE_ID

        gfr_patcher = patch(f"{MODULE}.getFilesRelease")
        self.mock_gfr_class = gfr_patcher.start()
        self.addCleanup(gfr_patcher.stop)
        self.mock_gfr = MagicMock()
        self.mock_gfr_class.return_value = self.mock_gfr

        of_patcher = patch(f"{MODULE}.outputFiles")
        self.mock_of_class = of_patcher.start()
        self.addCleanup(of_patcher.stop)
        self.mock_of = MagicMock()
        _configure_output_files_mock(self.mock_of, self.test_dir)
        self.mock_of_class.return_value = self.mock_of

        vds_patcher = patch(f"{MODULE}.ValDataStore")
        self.mock_vds_class = vds_patcher.start()
        self.addCleanup(vds_patcher.stop)
        self.mock_vds = MagicMock()
        self.mock_vds.isValidationRunning.return_value = False
        self.mock_vds_class.return_value = self.mock_vds

    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir, ignore_errors=True)


class StaticAndSimpleMethodTests(BaseValidateReleaseTest):
    def test_exptl_is_em_true_for_electron_microscopy(self) -> None:
        self.assertTrue(runValidation.exptl_is_em(["ELECTRON MICROSCOPY"]))

    def test_exptl_is_em_true_for_electron_crystallography(self) -> None:
        self.assertTrue(runValidation.exptl_is_em(["ELECTRON CRYSTALLOGRAPHY"]))

    def test_exptl_is_em_false_for_other_methods(self) -> None:
        self.assertFalse(runValidation.exptl_is_em(["X-RAY DIFFRACTION"]))

    def test_get_emdb_pdb_string_both_set(self) -> None:
        rv = runValidation()
        rv.setPdbId("1abc")
        rv.setEmdbId("EMD-1234")
        self.assertEqual(rv.get_emdb_pdb_string(), "EMD-1234-1abc")

    def test_get_emdb_pdb_string_pdb_only(self) -> None:
        rv = runValidation()
        rv.setPdbId("1abc")
        self.assertEqual(rv.get_emdb_pdb_string(), "")

    def test_get_emdb_pdb_string_neither_set(self) -> None:
        rv = runValidation()
        self.assertEqual(rv.get_emdb_pdb_string(), "")

    def test_set_entry_id_prefers_pdbid(self) -> None:
        rv = runValidation()
        rv.setPdbId("1abc")
        rv.setEmdbId("EMD-1234")
        self.assertTrue(rv.set_entry_id())
        self.assertEqual(rv.getEntryId(), "1abc")

    def test_set_entry_id_falls_back_to_emdbid(self) -> None:
        rv = runValidation()
        rv.setEmdbId("EMD-1234")
        self.assertTrue(rv.set_entry_id())
        self.assertEqual(rv.getEntryId(), "EMD-1234")

    def test_set_entry_id_fails_when_neither_set(self) -> None:
        rv = runValidation()
        self.assertFalse(rv.set_entry_id())

    def test_getters_reflect_setters(self) -> None:
        rv = runValidation()
        rv.setPdbId("1abc")
        rv.setEmdbId("EMD-1234")
        self.assertEqual(rv.getPDBId(), "1abc")
        self.assertEqual(rv.getEMDBId(), "EMD-1234")


class ProcessMessageTests(BaseValidateReleaseTest):
    def test_site_id_defaults_via_get_site_id(self) -> None:
        rv = runValidation()
        rv.process_message({})
        self.mock_get_site_id.assert_called()
        self.assertEqual(rv.get_siteId(), SITE_ID)

    def test_explicit_site_id_skips_get_site_id(self) -> None:
        rv = runValidation()
        self.mock_get_site_id.reset_mock()
        rv.process_message({"siteID": "OTHER_SITE"})
        self.mock_get_site_id.assert_not_called()
        self.assertEqual(rv.get_siteId(), "OTHER_SITE")

    def test_pdbid_lowercased(self) -> None:
        rv = runValidation()
        rv.process_message({"pdbID": "1ABC", "siteID": SITE_ID})
        self.assertEqual(rv.getPDBId(), "1abc")

    def test_emdbid_uppercased(self) -> None:
        rv = runValidation()
        rv.process_message({"emdbID": "emd-1234", "siteID": SITE_ID})
        self.assertEqual(rv.getEMDBId(), "EMD-1234")

    def test_output_root_sets_alternative_output_folder(self) -> None:
        rv = runValidation()
        rv.process_message({"outputRoot": "/out", "siteID": SITE_ID})
        # Verified indirectly: is_ok_to_copy short-circuits True when alternative folder set
        self.assertTrue(rv.is_ok_to_copy())

    def test_no_output_root_leaves_alternative_output_folder_false(self) -> None:
        rv = runValidation()
        rv.process_message({"siteID": SITE_ID, "alwaysRecalculate": True})
        # alwaysRecalculate short-circuits True too, so flip it off to check alternate folder default
        rv.setAlwaysRecalculate(False)
        # Nested (not parenthesized-combined) `with` statements: the combined form
        # is only valid syntax from Python 3.9+, and this file targets 3.8.
        with patch.object(rv, "get_start_end_cut_off", return_value=(None, None)):  # noqa: SIM117
            with patch(f"{MODULE}.ok_to_copy", return_value=False):
                self.assertFalse(rv.is_ok_to_copy())

    def test_setup_rel_files_rebuilt_with_new_site_id(self) -> None:
        rv = runValidation()
        self.mock_gfr_class.reset_mock()
        rv.process_message({"siteID": "OTHER_SITE"})
        self.mock_gfr_class.assert_called_once_with(siteID="OTHER_SITE", cache=None)
        self.mock_gfr.close_connections.assert_called_once()


class LazyLoadTests(BaseValidateReleaseTest):
    def test_get_model_path_lazily_sets_via_rel_files(self) -> None:
        self.mock_gfr.get_model.return_value = "model.cif"
        rv = runValidation()
        rv.setPdbId("1abc")
        self.assertEqual(rv.getModelPath(), "model.cif")
        self.mock_gfr.set_pdb_id.assert_called_once_with("1abc")

    def test_get_model_path_uses_cached_value(self) -> None:
        rv = runValidation()
        rv.setModelPath("cached.cif")
        self.assertEqual(rv.getModelPath(), "cached.cif")
        self.mock_gfr.get_model.assert_not_called()

    def test_get_em_xml_path_lazily_sets_via_rel_files(self) -> None:
        self.mock_gfr.get_emdb_xml.return_value = "emd.xml"
        rv = runValidation()
        rv.setEmdbId("EMD-1234")
        self.assertEqual(rv.getEMXMLPath(), "emd.xml")
        self.mock_gfr.set_emdb_id.assert_called_once_with("EMD-1234")

    def test_get_em_xml_path_uses_cached_value(self) -> None:
        rv = runValidation()
        rv.setEmXmlPath("cached.xml")
        self.assertEqual(rv.getEMXMLPath(), "cached.xml")
        self.mock_gfr.get_emdb_xml.assert_not_called()


class RunProcessTests(BaseValidateReleaseTest):
    def _message(self, **overrides: Any) -> Dict[str, Any]:
        message: Dict[str, Any] = {"siteID": SITE_ID}
        message.update(overrides)
        return message

    def test_run_process_returns_false_when_no_entry_id(self) -> None:
        rv = runValidation()
        ret = rv.run_process(self._message())
        self.assertFalse(ret)
        self.mock_gfr.remove_local_temp_files.assert_called_once()

    def test_run_process_remove_validation_files_short_circuits(self) -> None:
        rv = runValidation()
        with patch.object(rv, "remove_existing_files") as mock_remove, patch.object(
            rv, "run_validation"
        ) as mock_run_validation:
            ret = rv.run_process(self._message(pdbID="1abc", removeValFiles=True))
        self.assertTrue(ret)
        mock_remove.assert_called_once()
        mock_run_validation.assert_not_called()

    def test_run_process_raises_when_statefolder_not_set(self) -> None:
        self.mock_of.get_root_state_folder.return_value = None
        rv = runValidation()
        with self.assertRaises(ValueError):
            rv.run_process(self._message(pdbID="1abc"))

    def test_run_process_skips_when_already_running(self) -> None:
        self.mock_vds.isValidationRunning.return_value = True
        rv = runValidation()
        with patch.object(rv, "run_validation") as mock_run_validation:
            ret = rv.run_process(self._message(pdbID="1abc"))
        self.assertTrue(ret)
        mock_run_validation.assert_not_called()

    def test_run_process_pdb_only_success(self) -> None:
        rv = runValidation()
        self.mock_gfr.get_exp_methods = MagicMock()
        with patch.object(rv, "run_validation", return_value=(True, True)) as mock_run_validation, patch(
            f"{MODULE}.mmCIFInfo"
        ) as mock_mmcifinfo_class:
            mock_mmcifinfo_class.return_value.get_exp_methods.return_value = ["X-RAY DIFFRACTION"]
            ret = rv.run_process(self._message(pdbID="1abc"))
        self.assertTrue(ret)
        mock_run_validation.assert_called_once()
        self.assertIsNone(rv.getEMDBId())

    def test_run_process_pdb_triggers_associated_emdb(self) -> None:
        rv = runValidation()
        with patch.object(rv, "run_validation", return_value=(True, True)) as mock_run_validation, patch(
            f"{MODULE}.mmCIFInfo"
        ) as mock_mmcifinfo_class:
            mock_mmcifinfo_class.return_value.get_exp_methods.return_value = ["ELECTRON MICROSCOPY"]
            mock_mmcifinfo_class.return_value.get_associated_emdb.return_value = "EMD-9999"
            ret = rv.run_process(self._message(pdbID="1abc"))
        self.assertTrue(ret)
        self.assertEqual(rv.getEMDBId(), "EMD-9999")
        mock_run_validation.assert_called_once()

    def test_run_process_pdb_skip_emdb_flag_prevents_association(self) -> None:
        rv = runValidation()
        with patch.object(rv, "run_validation", return_value=(True, True)), patch(
            f"{MODULE}.mmCIFInfo"
        ) as mock_mmcifinfo_class:
            mock_mmcifinfo_class.return_value.get_exp_methods.return_value = ["ELECTRON MICROSCOPY"]
            mock_mmcifinfo_class.return_value.get_associated_emdb.return_value = "EMD-9999"
            ret = rv.run_process(self._message(pdbID="1abc", skip_emdb=True))
        self.assertTrue(ret)
        self.assertIsNone(rv.getEMDBId())

    def test_run_process_emdb_only_no_volume_no_map_only(self) -> None:
        # Nothing to run (no pdbid, no volume => no map-only pass) means
        # all_worked stays empty, which run_process treats as overall failure.
        self.mock_gfr.get_emdb_volume.return_value = None
        self.mock_gfr.get_emdb_xml.return_value = None
        rv = runValidation()
        with patch.object(rv, "run_validation", return_value=(True, True)) as mock_run_validation:
            ret = rv.run_process(self._message(emdbID="EMD-1234"))
        self.assertFalse(ret)
        mock_run_validation.assert_not_called()

    def test_run_process_emdb_with_volume_runs_map_only(self) -> None:
        self.mock_gfr.get_emdb_volume.return_value = "emd.map"
        self.mock_gfr.get_emdb_xml.return_value = None
        rv = runValidation()
        with patch.object(rv, "run_validation", return_value=(True, True)) as mock_run_validation:
            ret = rv.run_process(self._message(emdbID="EMD-1234"))
        self.assertTrue(ret)
        mock_run_validation.assert_called_once()

    def test_run_process_associated_pdbids_from_xml_are_run(self) -> None:
        self.mock_gfr.get_emdb_volume.return_value = "emd.map"
        self.mock_gfr.get_emdb_xml.return_value = "emd.xml"
        self.mock_gfr.get_model.return_value = "model.cif"
        rv = runValidation()
        with patch.object(rv, "run_validation", return_value=(True, True)) as mock_run_validation, patch(
            f"{MODULE}.XmlInfo"
        ) as mock_xmlinfo_class:
            mock_xmlinfo_class.return_value.get_pdbids_from_xml.return_value = ["1ABC"]
            ret = rv.run_process(self._message(emdbID="EMD-1234"))
        self.assertTrue(ret)
        # once for the associated PDB entry, once for the map-only run
        self.assertEqual(mock_run_validation.call_count, 2)

    def test_run_process_overall_false_when_any_subrun_fails(self) -> None:
        rv = runValidation()
        with patch.object(rv, "run_validation", return_value=(False, True)) as mock_run_validation, patch(
            f"{MODULE}.mmCIFInfo"
        ) as mock_mmcifinfo_class:
            mock_mmcifinfo_class.return_value.get_exp_methods.return_value = ["X-RAY DIFFRACTION"]
            ret = rv.run_process(self._message(pdbID="1abc"))
        self.assertFalse(ret)
        mock_run_validation.assert_called_once()

    def test_run_process_closes_connections_at_end(self) -> None:
        rv = runValidation()
        with patch.object(rv, "run_validation", return_value=(True, True)), patch(
            f"{MODULE}.mmCIFInfo"
        ) as mock_mmcifinfo_class:
            mock_mmcifinfo_class.return_value.get_exp_methods.return_value = ["X-RAY DIFFRACTION"]
            rv.run_process(self._message(pdbID="1abc"))
        self.mock_gfr.close_connections.assert_called()


class RunValidationTests(BaseValidateReleaseTest):
    """Bounded coverage of run_validation's own branches.

    check_modified/is_ok_to_copy are stubbed via patch.object since they each
    already have dedicated test coverage elsewhere; SessionManager, ValConfig,
    convert_cs_file, GenerateMinimalCif, and ValidationRun are mocked here so
    no real session/validation-wrapper/wwpdb.apps.validation code runs.
    """

    def setUp(self) -> None:
        super().setUp()
        self.session_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.session_dir, True)

        vc_patcher = patch(f"{MODULE}.ValConfig")
        mock_vc_class = vc_patcher.start()
        self.addCleanup(vc_patcher.stop)
        self.mock_vc = MagicMock()
        self.mock_vc.top_session_path = self.session_dir
        mock_vc_class.return_value = self.mock_vc

        sm_patcher = patch(f"{MODULE}.SessionManager")
        mock_sm_class = sm_patcher.start()
        self.addCleanup(sm_patcher.stop)
        self.mock_sm = MagicMock()
        self.mock_sm.makeSessionPath.return_value = self.session_dir
        mock_sm_class.return_value = self.mock_sm

        vr_patcher = patch(f"{MODULE}.ValidationRun")
        self.mock_vr_class = vr_patcher.start()
        self.addCleanup(vr_patcher.stop)
        self.mock_vr = MagicMock()
        self.mock_vr.run.return_value = []
        self.mock_vr_class.return_value = self.mock_vr

        cs_patcher = patch(f"{MODULE}.convert_cs_file")
        self.mock_convert_cs_file = cs_patcher.start()
        self.addCleanup(cs_patcher.stop)
        self.mock_convert_cs_file.return_value = None

        minimal_cif_patcher = patch(f"{MODULE}.GenerateMinimalCif")
        self.mock_minimal_cif_class = minimal_cif_patcher.start()
        self.addCleanup(minimal_cif_patcher.stop)

        # getFilesRelease's public getters return plain Optional[str] values
        # (not tuples); default them all to None/falsy so a test that only
        # cares about one code path doesn't accidentally trip an unrelated
        # branch (e.g. a truthy MagicMock default for get_nmr_data would
        # otherwise look like a real CS/nmr-data file being present).
        self.mock_gfr.get_model.return_value = "model.cif"
        self.mock_gfr.get_sf.return_value = None
        self.mock_gfr.get_cs.return_value = None
        self.mock_gfr.get_nmr_data.return_value = None
        self.mock_gfr.get_emdb_xml.return_value = None
        self.mock_gfr.get_emdb_volume.return_value = None
        self.mock_gfr.get_emdb_fsc.return_value = None

    def _make_rv(self, pdbid: Optional[str] = "1abc", emdbid: Optional[str] = None) -> runValidation:
        rv = runValidation()
        rv.process_message({"siteID": SITE_ID, "pdbID": pdbid, "emdbID": emdbid})
        return rv

    def test_run_validation_uses_site_id_as_python_site_id_by_default(self) -> None:
        rv = self._make_rv(pdbid="1abc", emdbid=None)
        with patch.object(rv, "check_modified", return_value=True), patch.object(
            rv, "is_ok_to_copy", return_value=True
        ):
            rv.run_validation()
        self.mock_vr_class.assert_called_once_with(siteId=SITE_ID, verbose=False, log=sys.stderr)

    def test_run_validation_uses_explicit_python_site_id(self) -> None:
        rv = runValidation()
        rv.process_message({"siteID": SITE_ID, "pdbID": "1abc", "python_site_id": "PY_SITE"})
        with patch.object(rv, "check_modified", return_value=True), patch.object(
            rv, "is_ok_to_copy", return_value=True
        ):
            rv.run_validation()
        self.mock_vr_class.assert_called_once_with(siteId="PY_SITE", verbose=False, log=sys.stderr)

    def test_run_validation_short_circuits_when_not_modified(self) -> None:
        rv = self._make_rv()
        with patch.object(rv, "check_modified", return_value=False):
            worked, validation_ran = rv.run_validation()
        self.assertTrue(worked)
        self.assertFalse(validation_ran)
        self.mock_vr.run.assert_not_called()

    def test_run_validation_happy_path_pdb_only(self) -> None:
        rv = self._make_rv(pdbid="1abc", emdbid=None)
        with patch.object(rv, "check_modified", return_value=True), patch.object(
            rv, "is_ok_to_copy", return_value=True
        ):
            worked, validation_ran = rv.run_validation()
        self.assertTrue(worked)
        self.assertTrue(validation_ran)
        self.mock_vr.run.assert_called_once()
        data_dict = self.mock_vr.run.call_args[0][0]
        self.assertEqual(data_dict["pdb_id"], "1abc")
        self.assertIsNone(data_dict["emdb_id"])

    def test_run_validation_cs_conversion_failure_returns_false(self) -> None:
        self.mock_gfr.get_nmr_data.return_value = "cs_or_nmr_path"
        self.mock_convert_cs_file.return_value = None
        rv = self._make_rv(pdbid="1abc", emdbid=None)
        with patch.object(rv, "check_modified", return_value=True):
            worked, validation_ran = rv.run_validation()
        self.assertFalse(worked)
        self.assertFalse(validation_ran)
        self.mock_vr.run.assert_not_called()

    def test_run_validation_exception_returns_false_false(self) -> None:
        self.mock_vr.run.side_effect = RuntimeError("boom")
        rv = self._make_rv(pdbid="1abc", emdbid=None)
        with patch.object(rv, "check_modified", return_value=True), patch.object(
            rv, "is_ok_to_copy", return_value=True
        ):
            worked, validation_ran = rv.run_validation()
        self.assertFalse(worked)
        self.assertFalse(validation_ran)

    def test_run_validation_map_only_generates_minimal_cif(self) -> None:
        self.mock_gfr.get_emdb_xml.return_value = "emd.xml"
        rv = self._make_rv(pdbid=None, emdbid="EMD-1234")
        rv.setEmXmlPath("emd.xml")
        with patch.object(rv, "check_modified", return_value=True), patch.object(
            rv, "is_ok_to_copy", return_value=True
        ):
            worked, validation_ran = rv.run_validation()
        self.assertTrue(worked)
        self.assertTrue(validation_ran)
        self.mock_minimal_cif_class.assert_called_once_with(emdb_xml="emd.xml")
        self.mock_minimal_cif_class.return_value.write_out.assert_called_once()

    # def test_run_validation_copies_to_emdb_when_both_ids_set(self) -> None:
    #     rv = self._make_rv(pdbid="1abc", emdbid="EMD-1234")
    #     with patch.object(rv, "check_modified", return_value=True), patch.object(
    #         rv, "is_ok_to_copy", return_value=True
    #     ), patch.object(rv, "copy_to_emdb", return_value=True) as mock_copy_to_emdb:
    #         worked, validation_ran = rv.run_validation()
    #     self.assertTrue(worked)
    #     self.assertTrue(validation_ran)
    #     mock_copy_to_emdb.assert_called_once()

    # def test_run_validation_copy_to_emdb_failure_returns_false(self) -> None:
    #     rv = self._make_rv(pdbid="1abc", emdbid="EMD-1234")
    #     with patch.object(rv, "check_modified", return_value=True), patch.object(
    #         rv, "is_ok_to_copy", return_value=True
    #     ), patch.object(rv, "copy_to_emdb", return_value=False):
    #         worked, validation_ran = rv.run_validation()
    #     self.assertFalse(worked)
    #     self.assertTrue(validation_ran)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
