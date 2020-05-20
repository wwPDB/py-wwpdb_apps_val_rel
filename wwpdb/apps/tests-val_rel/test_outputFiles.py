import unittest
import os
from wwpdb.apps.val_rel.utils.outputFiles import outputFiles


class OutputFilesTests(unittest.TestCase):
    def setUp(self):
        self.pdbid = "1cbs"
        self.pdbid_hash = self.pdbid[1:3]
        self.emdbid = "EMD-1234"
        self.emdb_accession = "emd_1234"
        self.emdb_accession_hyphen = "emd-1234"
        self.output_folder = os.path.join(os.sep, "nfs", "test")
        self.final_pdb_output_folder = os.path.join(
            self.output_folder, self.pdbid_hash, self.pdbid
        )
        self.final_emdb_output_folder = os.path.join(self.output_folder, self.emdbid)
        self.pdb_core_files = {
            "xml": os.path.join(
                self.final_pdb_output_folder, self.pdbid + "_validation.xml"
            ),
            "pdf": os.path.join(
                self.final_pdb_output_folder, self.pdbid + "_validation.pdf"
            ),
            "full_pdf": os.path.join(
                self.final_pdb_output_folder, self.pdbid + "_full_validation.pdf"
            ),
            "png": os.path.join(
                self.final_pdb_output_folder,
                self.pdbid + "_multipercentile_validation.png",
            ),
            "svg": os.path.join(
                self.final_pdb_output_folder,
                self.pdbid + "_multipercentile_validation.svg",
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
        self.emdb_core_files = {
            "xml": os.path.join(
                self.final_emdb_output_folder, self.emdb_accession + "_validation.xml"
            ),
            "pdf": os.path.join(
                self.final_emdb_output_folder, self.emdb_accession + "_validation.pdf"
            ),
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

    def test_get_dir(self):
        final_output_folder = ""
        of = outputFiles(outputRoot=self.output_folder)
        ret = of.get_entry_output_folder()
        self.assertTrue(ret == final_output_folder)

    def test_get_pdbid_dir(self):
        of = outputFiles(pdbID=self.pdbid, outputRoot=self.output_folder)
        ret = of.get_entry_output_folder()
        self.assertTrue(ret == self.final_pdb_output_folder)

    def test_get_emdb_dir(self):
        of = outputFiles(emdbID=self.emdbid, outputRoot=self.output_folder)
        ret = of.get_entry_output_folder()
        self.assertTrue(ret == self.final_emdb_output_folder)

    def test_get_pdbid_and_emdb_dir(self):
        of = outputFiles(pdbID=self.pdbid, outputRoot=self.output_folder)
        ret = of.get_entry_output_folder()
        self.assertTrue(ret == self.final_pdb_output_folder)

    def test_get_pdbid_dir_skip_hash(self):
        final_output_folder = os.path.join(self.output_folder, self.pdbid)
        of = outputFiles(
            pdbID=self.pdbid, outputRoot=self.output_folder, skip_pdb_hash=True
        )
        ret = of.get_entry_output_folder()
        self.assertTrue(ret == final_output_folder)

    def test_get_pdbid_dir_emdb_set_first(self):
        of = outputFiles(emdbID=self.emdbid, outputRoot=self.output_folder)
        of.set_pdb_id(entry_id=self.pdbid)
        ret = of.get_entry_output_folder()
        self.assertTrue(ret == self.final_pdb_output_folder)

    def test_set_accession_pdbid(self):
        of = outputFiles(pdbID=self.pdbid)
        ret = of.set_accession()
        self.assertTrue(ret == self.pdbid)

    def test_set_accession_emdbid(self):
        of = outputFiles(emdbID=self.emdbid)
        ret = of.set_accession()
        self.assertEqual(ret, self.emdb_accession)

    def test_set_accession_pdbid_and_not_set_emdbid(self):
        of = outputFiles(pdbID=self.pdbid, emdbID=self.emdbid)
        ret = of.set_accession()
        self.assertTrue(ret == self.pdbid)

    def test_set_accession_pdbid_and_emdbid(self):
        of = outputFiles(pdbID=self.pdbid, emdbID=self.emdbid)
        of.set_accession_variables(with_emdb=True)
        ret = of.set_accession()
        accession = "{}_{}".format(self.emdb_accession, self.pdbid)
        self.assertEqual(ret, accession)

    def test_set_accession_pdbid_get_core_files(self):
        of = outputFiles(pdbID=self.pdbid, outputRoot=self.output_folder)
        of.set_accession()
        ret = of.get_core_validation_files()
        self.assertTrue(ret == self.pdb_core_files)

    def test_set_accession_pdbid_get_map_files(self):
        of = outputFiles(pdbID=self.pdbid, outputRoot=self.output_folder)
        of.set_accession()
        ret = of.get_extra_validation_files()
        self.assertTrue(ret == self.pdb_aux_files)

    def test_set_accession_emdbid_get_core_files(self):
        of = outputFiles(emdbID=self.emdbid, outputRoot=self.output_folder)
        of.set_accession()
        ret = of.get_core_validation_files()
        self.assertEqual(ret, self.emdb_core_files)


if __name__ == "__main__":
    unittest.main()
