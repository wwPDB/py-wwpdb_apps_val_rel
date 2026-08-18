import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from wwpdb.apps.val_rel.utils.getFilesReleaseOneDep import getFilesReleaseOneDep

SITE_ID = "WWPDB_DEPLOY_TEST"


class GetFilesReleaseOneDepTests(unittest.TestCase):
    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()
        self.added_path = os.path.join(self.test_dir, "added")
        self.modified_path = os.path.join(self.test_dir, "modified")
        self.previous_added_path = os.path.join(self.test_dir, "previous", "added")
        self.previous_modified_path = os.path.join(self.test_dir, "previous", "modified")
        self.emd_current_path = os.path.join(self.test_dir, "emd", "header")
        self.emd_previous_path = os.path.join(self.test_dir, "previous", "emd", "header")

        rp_patcher = patch("wwpdb.apps.val_rel.utils.getFilesReleaseOneDep.ReleasePathInfo")
        mock_rp_class = rp_patcher.start()
        self.addCleanup(rp_patcher.stop)
        self.mock_rp = MagicMock()
        mock_rp_class.return_value = self.mock_rp
        self.mock_rp.get_added_path.return_value = self.added_path
        self.mock_rp.get_modified_path.return_value = self.modified_path
        self.mock_rp.get_previous_added_path.return_value = self.previous_added_path
        self.mock_rp.get_previous_modified_path.return_value = self.previous_modified_path
        self.mock_rp.get_emd_subfolder_path.return_value = self.emd_current_path
        self.mock_rp.get_previous_emd_subfolder_path.return_value = self.emd_previous_path

        rf_patcher = patch("wwpdb.apps.val_rel.utils.getFilesReleaseOneDep.ReleaseFileNames")
        mock_rf_class = rf_patcher.start()
        self.addCleanup(rf_patcher.stop)
        self.mock_rf = MagicMock()
        mock_rf_class.return_value = self.mock_rf
        self.mock_rf.get_model.return_value = "1abc.cif"
        self.mock_rf.get_structure_factor.return_value = "1abc-sf.cif"
        self.mock_rf.get_chemical_shifts.return_value = "1abc_cs.str"
        self.mock_rf.get_nmr_data.return_value = "1abc_nmr-data.str"
        self.mock_rf.get_emdb_xml.return_value = "emd-1234_v3.xml"
        self.mock_rf.get_emdb_map.return_value = "emd_1234.map"
        self.mock_rf.get_emdb_fsc.return_value = "emd_1234_fsc.xml"

    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _make_file(self, *parts: str) -> str:
        path = os.path.join(*parts)
        os.makedirs(os.path.dirname(path))
        with open(path, "w") as fout:
            fout.write("data")
        return path

    def test_get_onedep_pdb_folder_paths(self) -> None:
        gf = getFilesReleaseOneDep(pdb_id="1abc", emdb_id=None, siteID=SITE_ID)
        self.assertEqual(gf._get_onedep_pdb_folder_paths(), [self.added_path, self.modified_path])  # noqa: SLF001 pylint: disable=protected-access

    def test_get_previous_onedep_pdb_folder_paths(self) -> None:
        gf = getFilesReleaseOneDep(pdb_id="1abc", emdb_id=None, siteID=SITE_ID)
        self.assertEqual(
            gf._get_previous_onedep_pdb_folder_paths(),  # noqa: SLF001 pylint: disable=protected-access
            [self.previous_added_path, self.previous_modified_path],
        )

    def test_get_onedep_pdb_file_paths(self) -> None:
        gf = getFilesReleaseOneDep(pdb_id="1abc", emdb_id=None, siteID=SITE_ID)
        ret = gf._get_onedep_pdb_file_paths(filename="1abc.cif")  # noqa: SLF001 pylint: disable=protected-access
        self.assertEqual(
            ret,
            [
                os.path.join(self.added_path, "1abc", "1abc.cif"),
                os.path.join(self.modified_path, "1abc", "1abc.cif"),
            ],
        )

    def test_get_onedep_pdb_file_paths_raises_without_pdb_id(self) -> None:
        gf = getFilesReleaseOneDep(pdb_id=None, emdb_id=None, siteID=SITE_ID)
        with self.assertRaises(ValueError):
            gf._get_onedep_pdb_file_paths(filename="1abc.cif")  # noqa: SLF001 pylint: disable=protected-access

    def test_get_onedep_previous_pdb_file_paths_raises_without_pdb_id(self) -> None:
        gf = getFilesReleaseOneDep(pdb_id=None, emdb_id=None, siteID=SITE_ID)
        with self.assertRaises(ValueError):
            gf._get_onedep_previous_pdb_file_paths(filename="1abc.cif")  # noqa: SLF001 pylint: disable=protected-access

    def test_check_onedep_pdb_file_paths_found_in_modified(self) -> None:
        gf = getFilesReleaseOneDep(pdb_id="1abc", emdb_id=None, siteID=SITE_ID)
        expected = self._make_file(self.modified_path, "1abc", "1abc.cif")
        ret = gf._check_onedep_pdb_file_paths(filename="1abc.cif")  # noqa: SLF001 pylint: disable=protected-access
        self.assertEqual(ret, expected)

    def test_check_onedep_pdb_file_paths_not_found(self) -> None:
        gf = getFilesReleaseOneDep(pdb_id="1abc", emdb_id=None, siteID=SITE_ID)
        ret = gf._check_onedep_pdb_file_paths(filename="1abc.cif")  # noqa: SLF001 pylint: disable=protected-access
        self.assertIsNone(ret)

    def test_check_pdb_current_then_previous_current(self) -> None:
        gf = getFilesReleaseOneDep(pdb_id="1abc", emdb_id=None, siteID=SITE_ID)
        expected = self._make_file(self.added_path, "1abc", "1abc.cif")
        ret = gf.check_pdb_current_then_previous(filename="1abc.cif")
        self.assertEqual(ret, (expected, True))

    def test_check_pdb_current_then_previous_previous(self) -> None:
        gf = getFilesReleaseOneDep(pdb_id="1abc", emdb_id=None, siteID=SITE_ID)
        expected = self._make_file(self.previous_added_path, "1abc", "1abc.cif")
        ret = gf.check_pdb_current_then_previous(filename="1abc.cif")
        self.assertEqual(ret, (expected, False))

    def test_check_pdb_current_then_previous_missing(self) -> None:
        gf = getFilesReleaseOneDep(pdb_id="1abc", emdb_id=None, siteID=SITE_ID)
        ret = gf.check_pdb_current_then_previous(filename="1abc.cif")
        self.assertEqual(ret, (None, False))

    def test_check_emdb_current_then_previous_current(self) -> None:
        gf = getFilesReleaseOneDep(pdb_id=None, emdb_id="EMD-1234", siteID=SITE_ID)
        expected = self._make_file(self.emd_current_path, "emd-1234_v3.xml")
        ret = gf.check_emdb_current_then_previous(filename="emd-1234_v3.xml", subfolder="header")
        self.assertEqual(ret, (expected, True))

    def test_check_emdb_current_then_previous_previous(self) -> None:
        gf = getFilesReleaseOneDep(pdb_id=None, emdb_id="EMD-1234", siteID=SITE_ID)
        expected = self._make_file(self.emd_previous_path, "emd-1234_v3.xml")
        ret = gf.check_emdb_current_then_previous(filename="emd-1234_v3.xml", subfolder="header")
        self.assertEqual(ret, (expected, False))

    def test_check_emdb_current_then_previous_missing(self) -> None:
        gf = getFilesReleaseOneDep(pdb_id=None, emdb_id="EMD-1234", siteID=SITE_ID)
        ret = gf.check_emdb_current_then_previous(filename="emd-1234_v3.xml", subfolder="header")
        self.assertEqual(ret, (None, False))

    def test_get_model(self) -> None:
        gf = getFilesReleaseOneDep(pdb_id="1abc", emdb_id=None, siteID=SITE_ID)
        expected = self._make_file(self.added_path, "1abc", "1abc.cif")
        ret = gf.get_model()
        self.mock_rf.get_model.assert_called_with("1abc", for_release=True)
        self.assertEqual(ret, (expected, True))

    def test_get_sf(self) -> None:
        gf = getFilesReleaseOneDep(pdb_id="1abc", emdb_id=None, siteID=SITE_ID)
        expected = self._make_file(self.added_path, "1abc", "1abc-sf.cif")
        ret = gf.get_sf()
        self.assertEqual(ret, (expected, True))

    def test_get_cs(self) -> None:
        gf = getFilesReleaseOneDep(pdb_id="1abc", emdb_id=None, siteID=SITE_ID)
        expected = self._make_file(self.added_path, "1abc", "1abc_cs.str")
        ret = gf.get_cs()
        self.assertEqual(ret, (expected, True))

    def test_get_nmr_data(self) -> None:
        gf = getFilesReleaseOneDep(pdb_id="1abc", emdb_id=None, siteID=SITE_ID)
        expected = self._make_file(self.added_path, "1abc", "1abc_nmr-data.str")
        ret = gf.get_nmr_data()
        self.assertEqual(ret, (expected, True))

    def test_get_emdb_xml(self) -> None:
        gf = getFilesReleaseOneDep(pdb_id=None, emdb_id="EMD-1234", siteID=SITE_ID)
        expected = self._make_file(self.emd_current_path, "emd-1234_v3.xml")
        ret = gf.get_emdb_xml()
        self.assertEqual(ret, (expected, True))
        self.mock_rp.get_emd_subfolder_path.assert_called_with(accession="EMD-1234", subfolder="header")

    def test_get_emdb_volume(self) -> None:
        gf = getFilesReleaseOneDep(pdb_id=None, emdb_id="EMD-1234", siteID=SITE_ID)
        expected = self._make_file(self.emd_current_path, "emd_1234.map")
        ret = gf.get_emdb_volume()
        self.assertEqual(ret, (expected, True))

    def test_get_emdb_fsc(self) -> None:
        gf = getFilesReleaseOneDep(pdb_id=None, emdb_id="EMD-1234", siteID=SITE_ID)
        expected = self._make_file(self.emd_current_path, "emd_1234_fsc.xml")
        ret = gf.get_emdb_fsc()
        self.assertEqual(ret, (expected, True))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
