import csv
import json
import os
import shutil
import tempfile
import unittest
from typing import Any
from unittest.mock import MagicMock, patch

from wwpdb.apps.val_rel.utils.check_results import CheckEntries, CheckResult, prepare_entries_and_check

SITE_ID = "WWPDB_DEPLOY_TEST"
MODULE = "wwpdb.apps.val_rel.utils.check_results"


def _gzip_name(path: str) -> str:
    return path + ".gz"


class CheckResultTests(unittest.TestCase):
    """Unit tests for CheckResult.

    runValidation (the wwpdb.apps.val_rel.ValidateRelease entry point) and
    ValidationXMLReader/is_simple_modification (which live under
    wwpdb.apps.validation) are all mocked, so these tests never call any real
    wwpdb.apps.validation method or touch real site config.
    """

    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()

        rv_patcher = patch(f"{MODULE}.runValidation")
        self.mock_rv_class = rv_patcher.start()
        self.addCleanup(rv_patcher.stop)
        self.mock_rv = MagicMock()
        self.mock_rv_class.return_value = self.mock_rv

        simple_mod_patcher = patch(f"{MODULE}.is_simple_modification")
        self.mock_is_simple_modification = simple_mod_patcher.start()
        self.addCleanup(simple_mod_patcher.stop)
        self.mock_is_simple_modification.return_value = False

        xml_reader_patcher = patch(f"{MODULE}.ValidationXMLReader")
        self.mock_xml_reader_class = xml_reader_patcher.start()
        self.addCleanup(xml_reader_patcher.stop)
        self.mock_xml_reader = MagicMock()
        self.mock_xml_reader.get_failed_programs.return_value = []
        self.mock_xml_reader_class.return_value = self.mock_xml_reader

    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _touch(self, name: str) -> str:
        path = os.path.join(self.test_dir, name)
        with open(path, "w") as fout:
            fout.write("data")
        return path

    def _configure_rv(
        self,
        model_path: Any = "model.cif",
        em_xml_path: Any = None,
        validation_xml: Any = None,
        output_files: Any = None,
        entry_id: str = "1abc",
    ) -> None:
        self.mock_rv.getModelPath.return_value = model_path
        self.mock_rv.getEMXMLPath.return_value = em_xml_path
        self.mock_rv.getValidationXml.return_value = validation_xml
        self.mock_rv.getCoreOutputFileDict.return_value = output_files or {}
        self.mock_rv.getEntryId.return_value = entry_id

    # -- is_expected_file_type ----------------------------------------------

    def test_is_expected_file_type_true_when_pdbid_set(self) -> None:
        cr = CheckResult(pdbid="1abc", emdbid=None)
        self.assertTrue(cr.is_expected_file_type("svg"))
        self.assertTrue(cr.is_expected_file_type("png"))

    def test_is_expected_file_type_false_for_svg_png_when_emdb_only(self) -> None:
        cr = CheckResult(pdbid=None, emdbid="EMD-1234")
        self.assertFalse(cr.is_expected_file_type("svg"))
        self.assertFalse(cr.is_expected_file_type("png"))

    def test_is_expected_file_type_true_for_other_types_when_emdb_only(self) -> None:
        cr = CheckResult(pdbid=None, emdbid="EMD-1234")
        self.assertTrue(cr.is_expected_file_type("pdf"))

    def test_is_expected_file_type_true_when_neither_set(self) -> None:
        cr = CheckResult(pdbid=None, emdbid=None)
        self.assertTrue(cr.is_expected_file_type("svg"))

    # -- check_entry: process_message wiring ---------------------------------

    def test_check_entry_calls_process_message_with_expected_dict(self) -> None:
        self._configure_rv(model_path=None, output_files={})
        cr = CheckResult(
            output_folder="/out", pdbid="1abc", emdbid=None, siteID=SITE_ID, validation_sub_folder="current"
        )
        cr.check_entry()
        self.mock_rv.process_message.assert_called_once_with(
            {
                "pdbID": "1abc",
                "emdbID": None,
                "outputRoot": "/out",
                "siteID": SITE_ID,
                "subfolder": "current",
            }
        )
        self.mock_rv.set_entry_id.assert_called_once()
        self.mock_rv.set_output_dir_and_files.assert_called_once()

    def test_check_entry_message_omits_site_id_when_none(self) -> None:
        self._configure_rv(model_path=None, output_files={})
        cr = CheckResult(pdbid="1abc", emdbid=None, siteID=None)
        cr.check_entry()
        message = self.mock_rv.process_message.call_args[0][0]
        self.assertNotIn("siteID", message)

    # -- check_entry: model / em xml lookups ----------------------------------

    def test_check_entry_gets_model_path_only_for_pdb(self) -> None:
        self._configure_rv(model_path="model.cif", em_xml_path=None, output_files={})
        cr = CheckResult(pdbid="1abc", emdbid=None)
        cr.check_entry()
        self.mock_rv.getModelPath.assert_called_once()
        self.mock_rv.getEMXMLPath.assert_not_called()

    def test_check_entry_gets_em_xml_path_only_for_emdb(self) -> None:
        self._configure_rv(model_path=None, em_xml_path="emd.xml", output_files={})
        cr = CheckResult(pdbid=None, emdbid="EMD-1234")
        cr.check_entry()
        self.mock_rv.getEMXMLPath.assert_called_once()
        self.mock_rv.getModelPath.assert_not_called()

    def test_check_entry_simple_modification_skips_file_checks(self) -> None:
        self._configure_rv(model_path="model.cif", em_xml_path=None, output_files={"pdf": "out.pdf"})
        self.mock_is_simple_modification.return_value = True
        cr = CheckResult(pdbid="1abc", emdbid=None)
        cr.check_entry()
        self.assertEqual(cr.get_expected_files(), {})
        self.assertEqual(cr.get_missing_files(), {})
        self.mock_xml_reader_class.assert_not_called()

    def test_check_entry_not_simple_modification_when_em_xml_present(self) -> None:
        # simple_modification is only computed when model_file is truthy and em_xml_file is falsy
        self._configure_rv(model_path="model.cif", em_xml_path="emd.xml", output_files={})
        cr = CheckResult(pdbid="1abc", emdbid="EMD-1234")
        cr.check_entry()
        self.mock_is_simple_modification.assert_not_called()

    # -- check_entry: expected/missing file bookkeeping ------------------------

    def test_check_entry_marks_missing_and_present_files(self) -> None:
        present = self._touch("1abc_validation.pdf.gz")
        missing_base = os.path.join(self.test_dir, "1abc_validation.xml")
        self._configure_rv(
            model_path="model.cif",
            output_files={"pdf": present[: -len(".gz")], "xml": missing_base},
            entry_id="1abc",
        )
        cr = CheckResult(pdbid="1abc", emdbid=None)
        cr.check_entry()
        self.assertEqual(cr.get_expected_files(), {"pdf": present, "xml": _gzip_name(missing_base)})
        self.assertEqual(cr.get_missing_files(), {"xml": [{"1abc": _gzip_name(missing_base)}]})

    def test_check_entry_excludes_unexpected_file_types_for_emdb_only(self) -> None:
        svg_base = os.path.join(self.test_dir, "emd_1234_multipercentile_validation.svg")
        self._configure_rv(model_path=None, output_files={"svg": svg_base}, entry_id="EMD-1234")
        cr = CheckResult(pdbid=None, emdbid="EMD-1234")
        cr.check_entry()
        self.assertEqual(cr.get_expected_files(), {})
        self.assertEqual(cr.get_missing_files(), {})

    def test_did_all_files_fail_true_when_all_missing(self) -> None:
        missing1 = os.path.join(self.test_dir, "1abc_validation.pdf")
        missing2 = os.path.join(self.test_dir, "1abc_validation.xml")
        self._configure_rv(model_path="model.cif", output_files={"pdf": missing1, "xml": missing2})
        cr = CheckResult(pdbid="1abc", emdbid=None)
        cr.check_entry()
        self.assertTrue(cr.did_all_files_fail())

    def test_did_all_files_fail_false_when_some_present(self) -> None:
        present = self._touch("1abc_validation.pdf.gz")
        missing = os.path.join(self.test_dir, "1abc_validation.xml")
        self._configure_rv(model_path="model.cif", output_files={"pdf": present[: -len(".gz")], "xml": missing})
        cr = CheckResult(pdbid="1abc", emdbid=None)
        cr.check_entry()
        self.assertFalse(cr.did_all_files_fail())

    def test_did_all_files_fail_false_when_none_missing(self) -> None:
        present = self._touch("1abc_validation.pdf.gz")
        self._configure_rv(model_path="model.cif", output_files={"pdf": present[: -len(".gz")]})
        cr = CheckResult(pdbid="1abc", emdbid=None)
        cr.check_entry()
        self.assertFalse(cr.did_all_files_fail())

    # -- check_failed_programs (via check_entry) -------------------------------

    def test_check_entry_parses_failed_programs_when_validation_xml_exists(self) -> None:
        validation_xml_gz = self._touch("1abc_validation.xml.gz")
        validation_xml_base = validation_xml_gz[: -len(".gz")]
        self._configure_rv(model_path="model.cif", validation_xml=validation_xml_base, output_files={})
        self.mock_xml_reader.get_failed_programs.return_value = ["molprobity"]
        cr = CheckResult(pdbid="1abc", emdbid=None)
        cr.check_entry()
        self.mock_xml_reader_class.assert_called_once_with(validation_xml_gz)
        self.assertEqual(cr.get_failed_programs(), ["molprobity"])

    def test_check_entry_skips_failed_programs_when_validation_xml_missing(self) -> None:
        missing_xml = os.path.join(self.test_dir, "1abc_validation.xml")
        self._configure_rv(model_path="model.cif", validation_xml=missing_xml, output_files={})
        cr = CheckResult(pdbid="1abc", emdbid=None)
        cr.check_entry()
        self.mock_xml_reader_class.assert_not_called()
        self.assertEqual(cr.get_failed_programs(), [])

    def test_check_entry_skips_failed_programs_when_no_validation_xml(self) -> None:
        self._configure_rv(model_path="model.cif", validation_xml=None, output_files={})
        cr = CheckResult(pdbid="1abc", emdbid=None)
        cr.check_entry()
        self.mock_xml_reader_class.assert_not_called()


class CheckEntriesTests(unittest.TestCase):
    """Unit tests for CheckEntries.

    ReleasePathInfo (site config), FindEntries, and CheckResult are all mocked
    so these tests never touch real site config or call into the validation
    pipeline that CheckResult wraps.
    """

    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()

        rpi_patcher = patch(f"{MODULE}.ReleasePathInfo")
        mock_rpi_class = rpi_patcher.start()
        self.addCleanup(rpi_patcher.stop)
        self.mock_rpi = MagicMock()
        self.mock_rpi.get_for_release_path.return_value = self.test_dir
        mock_rpi_class.return_value = self.mock_rpi

        fe_patcher = patch(f"{MODULE}.FindEntries")
        mock_fe_class = fe_patcher.start()
        self.addCleanup(fe_patcher.stop)
        self.mock_fe = MagicMock()
        self.mock_fe.get_added_pdb_entries.return_value = []
        self.mock_fe.get_modified_pdb_entries.return_value = []
        self.mock_fe.get_emdb_entries.return_value = []
        mock_fe_class.return_value = self.mock_fe

        cr_patcher = patch(f"{MODULE}.CheckResult")
        self.mock_cr_class = cr_patcher.start()
        self.addCleanup(cr_patcher.stop)

    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _mock_check_result(
        self, did_all_files_fail: bool = False, missing_files: Any = None, failed_programs: Any = None
    ) -> MagicMock:
        mock_cr = MagicMock()
        mock_cr.did_all_files_fail.return_value = did_all_files_fail
        mock_cr.get_missing_files.return_value = missing_files or {}
        mock_cr.get_failed_programs.return_value = failed_programs or []
        self.mock_cr_class.return_value = mock_cr
        return mock_cr

    # -- constructor / clear -------------------------------------------------

    def test_constructor_creates_release_path_info_with_site_id(self) -> None:
        with patch(f"{MODULE}.ReleasePathInfo") as mock_rpi_class:
            CheckEntries(siteID=SITE_ID)
            mock_rpi_class.assert_called_once_with(siteId=SITE_ID)

    def test_clear_entry_list_resets_state(self) -> None:
        ce = CheckEntries(siteID=SITE_ID)
        ce.add_pdb_entries(["1abc"])
        ce.failed_entries = {"pdb": {"1abc"}}
        ce.entries_with_failed_programs = ["1abc"]
        ce.clear_entry_list()
        self.assertEqual(ce.get_entry_list(), [])
        self.assertEqual(ce.get_failed_entries(), {})
        self.assertEqual(ce.get_entries_with_failed_programs(), [])
        self.assertEqual(ce.get_full_details(), {})

    def test_get_missing_file_path(self) -> None:
        ce = CheckEntries(siteID=SITE_ID)
        self.assertEqual(ce.get_missing_file_path(), os.path.join(self.test_dir, "missing.ids"))

    # -- read_missing_file ----------------------------------------------------

    def test_read_missing_file_missing_returns_empty(self) -> None:
        ce = CheckEntries(siteID=SITE_ID)
        self.assertEqual(ce.read_missing_file(), [])
        self.assertEqual(ce.get_entry_list(), [])

    def test_read_missing_file_reads_and_categorises_entries(self) -> None:
        missing_path = os.path.join(self.test_dir, "missing.ids")
        with open(missing_path, "w") as fout:
            writer = csv.DictWriter(fout, fieldnames=["entry_type", "entry_id"])
            writer.writeheader()
            writer.writerow({"entry_type": "pdb", "entry_id": "1abc"})
            writer.writerow({"entry_type": "emdb", "entry_id": "EMD-1234"})
        ce = CheckEntries(siteID=SITE_ID)
        ret = ce.read_missing_file()
        self.assertEqual(sorted(ret), ["1abc", "EMD-1234"])
        self.assertIn(("1abc", "pdb"), ce.get_entry_list())
        self.assertIn(("EMD-1234", "emdb"), ce.get_entry_list())

    def test_read_missing_file_malformed_csv_returns_empty(self) -> None:
        missing_path = os.path.join(self.test_dir, "missing.ids")
        with open(missing_path, "w") as fout:
            fout.write("not,the,right,columns\n1,2,3,4\n")
        ce = CheckEntries(siteID=SITE_ID)
        ret = ce.read_missing_file()
        self.assertEqual(ret, [])

    # -- write_missing_file ---------------------------------------------------

    def test_write_missing_file_writes_rows_for_failed_entries(self) -> None:
        ce = CheckEntries(siteID=SITE_ID)
        ce.failed_entries = {"pdb": {"1abc"}}
        ce.write_missing_file()
        with open(ce.get_missing_file_path()) as fin:
            rows = list(csv.DictReader(fin))
        self.assertEqual(rows, [{"entry_type": "pdb", "entry_id": "1abc"}])

    def test_write_missing_file_empty_when_no_failed_entries(self) -> None:
        ce = CheckEntries(siteID=SITE_ID)
        ce.write_missing_file()
        with open(ce.get_missing_file_path()) as fin:
            content = fin.read()
        self.assertEqual(content, "")

    # -- get_entries ------------------------------------------------------------

    def test_get_entries_uses_find_entries_by_default(self) -> None:
        self.mock_fe.get_added_pdb_entries.return_value = ["1abc"]
        self.mock_fe.get_modified_pdb_entries.return_value = ["2xyz"]
        self.mock_fe.get_emdb_entries.return_value = ["EMD-1234"]
        ce = CheckEntries(siteID=SITE_ID)
        ce.get_entries()
        self.assertEqual(
            sorted(ce.get_entry_list()),
            sorted([("1abc", "pdb"), ("2xyz", "pdb"), ("EMD-1234", "emdb")]),
        )

    def test_get_entries_skip_emdb(self) -> None:
        self.mock_fe.get_emdb_entries.return_value = ["EMD-1234"]
        ce = CheckEntries(siteID=SITE_ID)
        ce.get_entries(skip_emdb=True)
        self.assertEqual(ce.get_entry_list(), [])

    def test_get_entries_from_files_skips_find_entries(self) -> None:
        pdb_file = os.path.join(self.test_dir, "pdb_entries.txt")
        with open(pdb_file, "w") as fout:
            fout.write("1abc\n2xyz\n")
        ce = CheckEntries(siteID=SITE_ID)
        ce.get_entries(pdb_entry_file=pdb_file)
        self.assertEqual(ce.get_entry_list(), [("1abc", "pdb"), ("2xyz", "pdb")])
        self.mock_fe.get_added_pdb_entries.assert_not_called()

    def test_get_entries_from_emdb_file(self) -> None:
        emdb_file = os.path.join(self.test_dir, "emdb_entries.txt")
        with open(emdb_file, "w") as fout:
            fout.write("EMD-1234\n")
        ce = CheckEntries(siteID=SITE_ID)
        ce.get_entries(emdb_entry_file=emdb_file)
        self.assertEqual(ce.get_entry_list(), [("EMD-1234", "emdb")])

    # -- check_entries ------------------------------------------------------------

    def test_check_entries_empty_list_returns_empty_dict(self) -> None:
        ce = CheckEntries(siteID=SITE_ID)
        self.assertEqual(ce.check_entries(), {})
        self.mock_cr_class.assert_not_called()

    def test_check_entries_creates_check_result_for_pdb(self) -> None:
        self._mock_check_result()
        ce = CheckEntries(siteID=SITE_ID)
        ce.add_pdb_entries(["1abc"])
        ce.check_entries(output_folder="/out", validation_sub_folder="current")
        self.mock_cr_class.assert_called_once_with(
            output_folder="/out",
            pdbid="1abc",
            siteID=SITE_ID,
            validation_sub_folder="current",
        )

    def test_check_entries_creates_check_result_for_emdb(self) -> None:
        self._mock_check_result()
        ce = CheckEntries(siteID=SITE_ID)
        ce.add_emdb_entries(["EMD-1234"])
        ce.check_entries()
        self.mock_cr_class.assert_called_once_with(
            output_folder=None,
            emdbid="EMD-1234",
            siteID=SITE_ID,
            validation_sub_folder="current",
        )

    def test_check_entries_unknown_type_short_circuits(self) -> None:
        ce = CheckEntries(siteID=SITE_ID)
        ce.entry_list = [("1abc", "bogus"), ("2xyz", "pdb")]
        ret = ce.check_entries()
        self.assertEqual(ret, {})
        self.mock_cr_class.assert_not_called()

    def test_check_entries_records_failed_entries(self) -> None:
        self._mock_check_result(did_all_files_fail=True)
        ce = CheckEntries(siteID=SITE_ID)
        ce.add_pdb_entries(["1abc"])
        ce.check_entries()
        self.assertEqual(ce.get_failed_entries(), {"pdb": {"1abc"}})

    def test_check_entries_no_failed_entries_when_not_all_fail(self) -> None:
        self._mock_check_result(did_all_files_fail=False)
        ce = CheckEntries(siteID=SITE_ID)
        ce.add_pdb_entries(["1abc"])
        ce.check_entries()
        self.assertEqual(ce.get_failed_entries(), {})

    def test_check_entries_records_missing_output(self) -> None:
        self._mock_check_result(missing_files={"pdf": [{"1abc": "/out/1abc.pdf.gz"}]})
        ce = CheckEntries(siteID=SITE_ID)
        ce.add_pdb_entries(["1abc"])
        ce.check_entries()
        self.assertEqual(
            ce.get_missing_output(),
            {"pdb": {"pdf": [[{"1abc": "/out/1abc.pdf.gz"}]]}},
        )

    def test_check_entries_records_failed_programs(self) -> None:
        self._mock_check_result(failed_programs=["molprobity"])
        ce = CheckEntries(siteID=SITE_ID)
        ce.add_pdb_entries(["1abc"])
        ce.check_entries()
        self.assertEqual(ce.get_entries_with_failed_programs(), ["1abc"])
        self.assertEqual(ce.get_failed_programs(), {"molprobity": ["1abc"]})

    # -- write_missing_json / write_missing -----------------------------------

    def test_write_missing_json_empty(self) -> None:
        ce = CheckEntries(siteID=SITE_ID)
        output_file = os.path.join(self.test_dir, "out.json")
        ce.write_missing_json(output_file)
        with open(output_file) as fin:
            self.assertEqual(json.load(fin), {})

    def test_write_missing_writes_newline_joined_entries(self) -> None:
        ce = CheckEntries(siteID=SITE_ID)
        ce.failed_entries = {"pdb": {"1abc"}}
        output_file = os.path.join(self.test_dir, "out.txt")
        ce.write_missing(output_file)
        with open(output_file) as fin:
            self.assertEqual(fin.read(), "1abc\n")


class PrepareEntriesAndCheckTests(unittest.TestCase):
    """Unit tests for the prepare_entries_and_check module function.

    CheckEntries is mocked wholesale, so this only verifies the function's own
    branching logic, never real site config or validation calls.
    """

    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()
        ce_patcher = patch(f"{MODULE}.CheckEntries")
        self.mock_ce_class = ce_patcher.start()
        self.addCleanup(ce_patcher.stop)
        self.mock_ce = MagicMock()
        self.mock_ce.get_failed_entries.return_value = {}
        self.mock_ce.get_failed_programs.return_value = {}
        self.mock_ce.get_full_details.return_value = {}
        self.mock_ce_class.return_value = self.mock_ce

    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_output_folder_set_runs_single_pass(self) -> None:
        prepare_entries_and_check(siteID=SITE_ID, output_folder="/out")
        self.mock_ce.get_entries.assert_called_once_with(skip_emdb=False, pdb_entry_file=None, emdb_entry_file=None)
        self.mock_ce.check_entries.assert_called_once_with(output_folder="/out")

    def test_no_output_folder_checks_current_and_missing(self) -> None:
        prepare_entries_and_check(siteID=SITE_ID)
        self.assertEqual(self.mock_ce.get_entries.call_count, 1)
        self.assertEqual(self.mock_ce.read_missing_file.call_count, 1)
        self.assertEqual(self.mock_ce.check_entries.call_count, 2)
        self.assertEqual(self.mock_ce.clear_entry_list.call_count, 2)

    def test_validation_sub_folder_restricts_to_one_pass(self) -> None:
        prepare_entries_and_check(siteID=SITE_ID, validation_sub_folder="missing")
        self.mock_ce.read_missing_file.assert_called_once()
        self.mock_ce.get_entries.assert_not_called()
        self.mock_ce.check_entries.assert_called_once_with(validation_sub_folder="missing")

    def test_failed_entries_file_writes_output(self) -> None:
        output_file = os.path.join(self.test_dir, "failed.txt")
        prepare_entries_and_check(siteID=SITE_ID, output_folder="/out", failed_entries_file=output_file)
        self.mock_ce.write_missing.assert_called_once_with(output_file)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
