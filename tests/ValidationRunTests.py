import os
import shutil
import sys
import tempfile
import unittest
from typing import Any, Dict, List, Optional, Union
from unittest.mock import MagicMock, call, patch

from wwpdb.apps.val_rel.utils.ValidationRun import ValidationRun

SITE_ID = "WWPDB_DEPLOY_TEST"
MODULE = "wwpdb.apps.val_rel.utils.ValidationRun"

DDType = Dict[str, Union[Optional[str], Dict[str, str], bool]]


class ValidationRunTests(unittest.TestCase):
    """Unit tests for ValidationRun.

    Site config (ValConfig) and the validation pipeline itself (ValidationWrapper,
    which is what would otherwise reach into wwpdb.apps.validation) are both mocked,
    so these tests never contact real site configuration or run a real validation.
    """

    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()

        vc_patcher = patch(f"{MODULE}.ValConfig")
        self.mock_vc_class = vc_patcher.start()
        self.addCleanup(vc_patcher.stop)
        self.mock_vc = MagicMock()
        self.mock_vc.val_disable_multithread = False
        self.mock_vc_class.return_value = self.mock_vc

        vw_patcher = patch(f"{MODULE}.ValidationWrapper")
        self.mock_vw_class = vw_patcher.start()
        self.addCleanup(vw_patcher.stop)
        self.mock_vw = MagicMock()
        self.mock_vw.expList.return_value = True
        self.mock_vw_class.return_value = self.mock_vw

    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _touch(self, name: str) -> str:
        path = os.path.join(self.test_dir, name)
        with open(path, "w") as fout:
            fout.write("data")
        return path

    def _make_dD(self, **overrides: Any) -> DDType:
        dD: DDType = {
            "model": "model.cif",
            "sf": None,
            "cs": None,
            "res": None,
            "emvol": None,
            "emxml": None,
            "pdb_id": None,
            "emdb_id": None,
            "tempDir": self.test_dir,
            "entry_id": "1abc",
            "rundir": self.test_dir,
            "fsc": None,
            "keeplog": False,
            "logpath": None,
            "outfiledict": {},
            "entry_output_folder": self.test_dir,
        }
        dD.update(overrides)
        return dD

    def _addinput_calls(self) -> List[Dict[str, Any]]:
        return [c.kwargs for c in self.mock_vw.addInput.call_args_list]

    # -- constructor -------------------------------------------------------

    def test_constructor_reads_val_config(self) -> None:
        ValidationRun(siteId=SITE_ID)
        self.mock_vc_class.assert_called_once_with(SITE_ID)

    # -- ValidationWrapper construction ------------------------------------

    def test_run_builds_validation_wrapper_with_expected_args(self) -> None:
        vr = ValidationRun(siteId=SITE_ID)
        vr.run(self._make_dD())
        self.mock_vw_class.assert_called_once_with(
            tmpPath=self.test_dir,
            siteId=SITE_ID,
            verbose=False,
            log=sys.stderr,
        )

    def test_run_imports_model(self) -> None:
        vr = ValidationRun(siteId=SITE_ID)
        vr.run(self._make_dD(model="model.cif"))
        self.mock_vw.imp.assert_called_once_with("model.cif")

    def test_run_adds_run_dir_and_mode(self) -> None:
        vr = ValidationRun(siteId=SITE_ID)
        vr.run(self._make_dD(rundir="/run/dir"))
        self.assertIn({"name": "run_dir", "value": "/run/dir"}, self._addinput_calls())
        self.assertIn({"name": "request_validation_mode", "value": "release"}, self._addinput_calls())

    # -- entry_id / emdb_id branch -------------------------------------------

    def test_run_pdb_id_sets_entry_id_only(self) -> None:
        vr = ValidationRun(siteId=SITE_ID)
        vr.run(self._make_dD(pdb_id="1abc", emdb_id="EMD-1234"))
        calls = self._addinput_calls()
        self.assertIn({"name": "entry_id", "value": "1abc"}, calls)
        self.assertNotIn({"name": "emdb_id", "value": "EMD-1234"}, calls)

    def test_run_emdb_id_sets_entry_id_and_emdb_id(self) -> None:
        vr = ValidationRun(siteId=SITE_ID)
        vr.run(self._make_dD(pdb_id=None, emdb_id="EMD-1234"))
        calls = self._addinput_calls()
        self.assertIn({"name": "entry_id", "value": "EMD-1234"}, calls)
        self.assertIn({"name": "emdb_id", "value": "EMD-1234"}, calls)

    def test_run_neither_id_adds_no_entry_id(self) -> None:
        vr = ValidationRun(siteId=SITE_ID)
        vr.run(self._make_dD(pdb_id=None, emdb_id=None))
        names = [c["name"] for c in self._addinput_calls()]
        self.assertNotIn("entry_id", names)
        self.assertNotIn("emdb_id", names)

    # -- optional file inputs -------------------------------------------------

    def test_run_adds_all_optional_inputs_when_readable(self) -> None:
        sf = self._touch("model-sf.cif")
        cs = self._touch("model_cs.str")
        res = self._touch("model.mr")
        emvol = self._touch("emd.map")
        emxml = self._touch("emd.xml")
        fsc = self._touch("emd_fsc.xml")
        vr = ValidationRun(siteId=SITE_ID)
        vr.run(self._make_dD(sf=sf, cs=cs, res=res, emvol=emvol, emxml=emxml, fsc=fsc))
        calls = self._addinput_calls()
        self.assertIn({"name": "sf_file_path", "value": sf}, calls)
        self.assertIn({"name": "cs_file_path", "value": cs}, calls)
        self.assertIn({"name": "nmr_restraint_file_path", "value": res}, calls)
        self.assertIn({"name": "vol_file_path", "value": emvol}, calls)
        self.assertIn({"name": "emdb_xml_path", "value": emxml}, calls)
        self.assertIn({"name": "fsc_file_path", "value": fsc}, calls)

    def test_run_skips_optional_inputs_when_none(self) -> None:
        vr = ValidationRun(siteId=SITE_ID)
        vr.run(self._make_dD())
        names = [c["name"] for c in self._addinput_calls()]
        for optional_name in (
            "sf_file_path",
            "cs_file_path",
            "nmr_restraint_file_path",
            "vol_file_path",
            "emdb_xml_path",
            "fsc_file_path",
        ):
            self.assertNotIn(optional_name, names)

    def test_run_skips_optional_inputs_when_path_missing(self) -> None:
        missing = os.path.join(self.test_dir, "does_not_exist.cif")
        vr = ValidationRun(siteId=SITE_ID)
        vr.run(self._make_dD(sf=missing))
        names = [c["name"] for c in self._addinput_calls()]
        self.assertNotIn("sf_file_path", names)

    # -- disable multithread -------------------------------------------------

    def test_run_adds_skip_multi_when_disabled(self) -> None:
        self.mock_vc.val_disable_multithread = True
        vr = ValidationRun(siteId=SITE_ID)
        vr.run(self._make_dD())
        self.assertIn({"name": "skip_multi", "value": True}, self._addinput_calls())

    def test_run_omits_skip_multi_when_enabled(self) -> None:
        self.mock_vc.val_disable_multithread = False
        vr = ValidationRun(siteId=SITE_ID)
        vr.run(self._make_dD())
        names = [c["name"] for c in self._addinput_calls()]
        self.assertNotIn("skip_multi", names)

    # -- op / log -------------------------------------------------------------

    def test_run_calls_op_with_annot_validate_all_sf(self) -> None:
        vr = ValidationRun(siteId=SITE_ID)
        vr.run(self._make_dD())
        self.mock_vw.op.assert_called_once_with("annot-wwpdb-validate-all-sf")

    def test_run_keeplog_true_exports_log(self) -> None:
        vr = ValidationRun(siteId=SITE_ID)
        vr.run(self._make_dD(keeplog=True, logpath="/logs/out.log"))
        self.mock_vw.expLog.assert_called_once_with("/logs/out.log")

    def test_run_keeplog_false_skips_export_log(self) -> None:
        vr = ValidationRun(siteId=SITE_ID)
        vr.run(self._make_dD(keeplog=False))
        self.mock_vw.expLog.assert_not_called()

    # -- output file list / expList / cleanup --------------------------------

    def test_run_builds_output_file_list_in_order_with_missing_keys_none(self) -> None:
        outfiledict = {"pdf": "a.pdf", "xml": "a.xml", "cif": "a.cif"}
        vr = ValidationRun(siteId=SITE_ID)
        ret = vr.run(self._make_dD(outfiledict=outfiledict))
        self.assertEqual(ret, ["a.pdf", "a.xml", None, None, None, None, "a.cif", None, None])

    def test_run_calls_explist_with_output_file_list(self) -> None:
        outfiledict = {"pdf": "a.pdf"}
        vr = ValidationRun(siteId=SITE_ID)
        ret = vr.run(self._make_dD(outfiledict=outfiledict))
        self.mock_vw.expList.assert_called_once_with(dstPathList=ret)

    def test_run_explist_failure_does_not_raise(self) -> None:
        self.mock_vw.expList.return_value = False
        vr = ValidationRun(siteId=SITE_ID)
        vr.run(self._make_dD())  # should not raise

    def test_run_calls_cleanup(self) -> None:
        vr = ValidationRun(siteId=SITE_ID)
        vr.run(self._make_dD())
        self.mock_vw.cleanup.assert_called_once_with()

    def test_run_call_order_op_then_explist_then_cleanup(self) -> None:
        manager = MagicMock()
        manager.attach_mock(self.mock_vw.op, "op")
        manager.attach_mock(self.mock_vw.expList, "expList")
        manager.attach_mock(self.mock_vw.cleanup, "cleanup")
        vr = ValidationRun(siteId=SITE_ID)
        vr.run(self._make_dD())
        expected = [
            call.op("annot-wwpdb-validate-all-sf"),
            call.expList(dstPathList=[None] * 9),
            call.cleanup(),
        ]
        self.assertEqual(manager.mock_calls, expected)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
