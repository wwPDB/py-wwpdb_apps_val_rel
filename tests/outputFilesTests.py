import os
import unittest
from unittest.mock import patch

if __package__ is None or __package__ == "":
    import sys
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import (  # type: ignore[import-not-found]  # pylint: disable=import-error
        TESTOUTPUT,
        StandardConfig,
    )
else:
    from .commonsetup import (  # noqa: TID252  # pragma: no cover
        TESTOUTPUT,
        StandardConfig,
    )


from wwpdb.apps.val_rel.utils.outputFiles import outputFiles


class OutputFilesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.pdbid = "1cbs"
        self.pdbid_hash = self.pdbid[1:3]
        self.emdbid = "EMD-1234"
        self.emdb_accession = "emd_1234"
        self.emdb_accession_hyphen = "emd-1234"
        self.output_folder = os.path.join(os.sep, "nfs", "test")
        self.final_pdb_output_folder = os.path.join(self.output_folder, "pdb", self.pdbid_hash, self.pdbid)
        self.final_emdb_output_folder = os.path.join(self.output_folder, "emd", self.emdbid, "validation")
        self.pdb_core_files = {
            "xml": os.path.join(self.final_pdb_output_folder, self.pdbid + "_validation.xml"),
            "pdf": os.path.join(self.final_pdb_output_folder, self.pdbid + "_validation.pdf"),
            "full_pdf": os.path.join(self.final_pdb_output_folder, self.pdbid + "_full_validation.pdf"),
            "png": os.path.join(
                self.final_pdb_output_folder,
                self.pdbid + "_multipercentile_validation.png",
            ),
            "svg": os.path.join(
                self.final_pdb_output_folder,
                self.pdbid + "_multipercentile_validation.svg",
            ),
            "cif": os.path.join(
                self.final_pdb_output_folder,
                self.pdbid + "_validation.cif",
            ),
        }
        self.pdb_aux_files = {
            "fofc": os.path.join(
                self.final_pdb_output_folder,
                self.pdbid + "_validation_fo-fc_map_coef.cif",
            ),
            "2fofc": os.path.join(
                self.final_pdb_output_folder,
                self.pdbid + "_validation_2fo-fc_map_coef.cif",
            ),
        }
        self.for_release_path = os.path.join(TESTOUTPUT, "data", "for_release")
        self.emdb_core_files = {
            "cif": os.path.join(
                self.final_emdb_output_folder,
                self.emdb_accession + "_validation.cif",
            ),
            "xml": os.path.join(self.final_emdb_output_folder, self.emdb_accession + "_validation.xml"),
            "pdf": os.path.join(self.final_emdb_output_folder, self.emdb_accession + "_validation.pdf"),
            "full_pdf": os.path.join(
                self.final_emdb_output_folder,
                self.emdb_accession + "_full_validation.pdf",
            ),
            "png": os.path.join(
                self.final_emdb_output_folder,
                self.emdb_accession + "_multipercentile_validation.png",
            ),
            "svg": os.path.join(
                self.final_emdb_output_folder,
                self.emdb_accession + "_multipercentile_validation.svg",
            ),
        }

    def test_get_dir(self) -> None:
        with patch("wwpdb.utils.config.ConfigInfoApp.ConfigInfo", side_effect=StandardConfig) as _mock_method:  # noqa: F841
            of = outputFiles(outputRoot=self.output_folder)
            ret = of.get_entry_output_folder()
            self.assertIsNone(ret)

    def test_get_pdbid_dir(self) -> None:
        of = outputFiles(pdbID=self.pdbid, outputRoot=self.output_folder)
        ret = of.get_entry_output_folder()
        self.assertEqual(ret, self.final_pdb_output_folder)

    def test_get_emdb_dir(self) -> None:
        of = outputFiles(emdbID=self.emdbid, outputRoot=self.output_folder)
        ret = of.get_entry_output_folder()
        self.assertEqual(ret, self.final_emdb_output_folder)

    def test_get_pdbid_and_emdb_dir(self) -> None:
        of = outputFiles(pdbID=self.pdbid, outputRoot=self.output_folder)
        ret = of.get_entry_output_folder()
        self.assertEqual(ret, self.final_pdb_output_folder)

    def test_get_pdbid_dir_skip_hash(self) -> None:
        final_output_folder = os.path.join(self.output_folder, "pdb", self.pdbid)
        of = outputFiles(pdbID=self.pdbid, outputRoot=self.output_folder, skip_pdb_hash=True)
        ret = of.get_entry_output_folder()
        self.assertEqual(ret, final_output_folder)

    def test_get_pdbid_dir_emdb_set_first(self) -> None:
        of = outputFiles(emdbID=self.emdbid, outputRoot=self.output_folder)
        of.set_pdb_id(entry_id=self.pdbid)
        ret = of.get_entry_output_folder()
        self.assertEqual(ret, self.final_pdb_output_folder)

    def test_ret_pdb_hash_skip_hash(self) -> None:
        of = outputFiles(pdbID=self.pdbid, outputRoot=self.output_folder, skip_pdb_hash=True)
        ret = of.ret_pdb_hash()
        self.assertEqual(ret, "")

    def test_ret_pdb_hash(self) -> None:
        of = outputFiles(pdbID=self.pdbid, outputRoot=self.output_folder)
        ret = of.ret_pdb_hash()
        self.assertEqual(ret, self.pdbid_hash)

    def test_get_pdb_id_hash_no_pdbid(self) -> None:
        of = outputFiles(outputRoot=self.output_folder)
        self.assertEqual(of.get_pdb_id_hash(), "")

    def test_get_pdb_id_no_pdbid(self) -> None:
        of = outputFiles(outputRoot=self.output_folder)
        self.assertEqual(of.get_pdb_id(), "")

    def test_get_emdb_id_no_emdbid(self) -> None:
        of = outputFiles(outputRoot=self.output_folder)
        self.assertEqual(of.get_emdb_id(), "")

    def test_get_entry_id_not_set(self) -> None:
        of = outputFiles(outputRoot=self.output_folder)
        self.assertEqual(of.get_entry_id(), "")

    def test_get_entry_id_set_from_pdbid(self) -> None:
        of = outputFiles(pdbID=self.pdbid, outputRoot=self.output_folder)
        self.assertEqual(of.get_entry_id(), self.pdbid)

    def test_get_emdb_lower_hyphen(self) -> None:
        of = outputFiles(emdbID=self.emdbid, outputRoot=self.output_folder)
        self.assertEqual(of.get_emdb_lower_hyphen(), self.emdb_accession_hyphen)

    def test_get_emdb_lower_hyphen_no_emdbid(self) -> None:
        of = outputFiles(outputRoot=self.output_folder)
        self.assertEqual(of.get_emdb_lower_hyphen(), "")

    def test_get_emdb_lower_underscore_no_emdbid(self) -> None:
        of = outputFiles(outputRoot=self.output_folder)
        self.assertEqual(of.get_emdb_lower_underscore(), "")

    def test_get_pdb_validation_images_output_folder_with_root(self) -> None:
        of = outputFiles(pdbID=self.pdbid, outputRoot=self.output_folder)
        ret = of.get_pdb_validation_images_output_folder()
        self.assertEqual(ret, os.path.join(self.output_folder, "val_images", self.pdbid))

    def test_get_pdb_validation_images_output_folder_no_root(self) -> None:
        with patch("wwpdb.utils.config.ConfigInfoApp.ConfigInfo", side_effect=StandardConfig) as _mock_method:  # noqa: F841
            of = outputFiles(pdbID=self.pdbid)
            ret = of.get_pdb_validation_images_output_folder()
            expected = os.path.join(self.for_release_path, "val_images", self.pdbid)
            self.assertEqual(ret, expected)

    def test_get_pdb_root_folder(self) -> None:
        with patch("wwpdb.utils.config.ConfigInfoApp.ConfigInfo", side_effect=StandardConfig) as _mock_method:  # noqa: F841
            of = outputFiles()
            ret = of.get_pdb_root_folder()
            self.assertEqual(ret, os.path.join(self.for_release_path, "val_reports", "current"))

    def test_get_pdb_root_folder_custom_subdirectory(self) -> None:
        with patch("wwpdb.utils.config.ConfigInfoApp.ConfigInfo", side_effect=StandardConfig) as _mock_method:  # noqa: F841
            of = outputFiles(validation_sub_directory="previous")
            of.set_validation_subdirectory("previous")
            ret = of.get_pdb_root_folder()
            self.assertEqual(ret, os.path.join(self.for_release_path, "val_reports", "previous"))

    def test_get_emdb_root_folder(self) -> None:
        with patch("wwpdb.utils.config.ConfigInfoApp.ConfigInfo", side_effect=StandardConfig) as _mock_method:  # noqa: F841
            of = outputFiles()
            ret = of.get_emdb_root_folder()
            self.assertEqual(ret, os.path.join(self.for_release_path, "em_val_reports", "current"))

    def test_get_validation_images_root_folder(self) -> None:
        with patch("wwpdb.utils.config.ConfigInfoApp.ConfigInfo", side_effect=StandardConfig) as _mock_method:  # noqa: F841
            of = outputFiles()
            ret = of.get_validation_images_root_folder()
            self.assertEqual(ret, os.path.join(self.for_release_path, "val_images"))

    def test_get_root_state_folder(self) -> None:
        with patch("wwpdb.utils.config.ConfigInfoApp.ConfigInfo", side_effect=StandardConfig) as _mock_method:  # noqa: F841
            of = outputFiles()
            ret = of.get_root_state_folder()
            self.assertEqual(ret, os.path.join(self.for_release_path, "val_reports", "current_state"))

    def test_get_ftp_cache_folder(self) -> None:
        with patch("wwpdb.utils.config.ConfigInfoApp.ConfigInfo", side_effect=StandardConfig) as _mock_method:  # noqa: F841
            of = outputFiles()
            ret = of.get_ftp_cache_folder()
            self.assertEqual(ret, os.path.join(self.for_release_path, "val_reports", "cache"))

    def test_get_pdb_output_folder_no_root(self) -> None:
        with patch("wwpdb.utils.config.ConfigInfoApp.ConfigInfo", side_effect=StandardConfig) as _mock_method:  # noqa: F841
            of = outputFiles(pdbID=self.pdbid)
            ret = of.get_pdb_output_folder()
            expected = os.path.join(self.for_release_path, "val_reports", "current", self.pdbid)
            self.assertEqual(ret, expected)

    def test_get_emdb_output_folder_no_root(self) -> None:
        with patch("wwpdb.utils.config.ConfigInfoApp.ConfigInfo", side_effect=StandardConfig) as _mock_method:  # noqa: F841
            of = outputFiles(emdbID=self.emdbid)
            ret = of.get_emdb_output_folder()
            expected = os.path.join(self.for_release_path, "em_val_reports", "current", self.emdbid, "validation")
            self.assertEqual(ret, expected)

    def test_add_output_folder_accession_no_entry_folder_raises(self) -> None:
        of = outputFiles()
        with self.assertRaises(ValueError):
            of.add_output_folder_accession("foo.xml")

    def test_add_output_folder_accession_temp_output_folder(self) -> None:
        temp_folder = os.path.join(os.sep, "tmp", "temp_output")
        of = outputFiles(pdbID=self.pdbid, outputRoot=self.output_folder, temp_output_folder=temp_folder)
        of.set_accession()
        ret = of.get_validation_xml()
        self.assertEqual(ret, os.path.join(temp_folder, self.pdbid + "_validation.xml"))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
