import unittest
import logging
import os
from wwpdb.apps.val_rel.outputFiles import outputFiles


class OutputFilesTests(unittest.TestCase):

    def setUp(self):
        self.pdbid = '1cbs'
        self.pdbid_hash = self.pdbid[1:3]
        self.emdbid = 'EMD-1234'
        self.emdb_accession = 'emd_1234'
        self.output_folder = os.path.join(os.sep, 'nfs', 'test')

    def test_get_dir(self):
        final_output_folder = ''
        of = outputFiles(outputRoot=self.output_folder)
        ret = of.get_entry_output_folder()
        self.assertTrue(ret == final_output_folder)

    def test_get_pdbid_dir(self):
        final_output_folder = os.path.join(self.output_folder, self.pdbid_hash, self.pdbid)
        of = outputFiles(pdbID=self.pdbid, outputRoot=self.output_folder)
        ret = of.get_entry_output_folder()
        self.assertTrue(ret == final_output_folder)

    def test_get_emdb_dir(self):
        final_output_folder = os.path.join(self.output_folder, 'emd', self.emdbid, 'validation')
        of = outputFiles(emdbID=self.emdbid, outputRoot=self.output_folder)
        ret = of.get_entry_output_folder()
        self.assertTrue(ret == final_output_folder)

    def test_get_pdbid_and_emdb_dir(self):
        final_output_folder = os.path.join(self.output_folder, self.pdbid_hash, self.pdbid)
        of = outputFiles(pdbID=self.pdbid, outputRoot=self.output_folder)
        ret = of.get_entry_output_folder()
        self.assertTrue(ret == final_output_folder)

    def test_get_pdbid_dir_skip_hash(self):
        final_output_folder = os.path.join(self.output_folder, self.pdbid)
        of = outputFiles(pdbID=self.pdbid, outputRoot=self.output_folder, skip_pdb_hash=True)
        ret = of.get_entry_output_folder()
        self.assertTrue(ret == final_output_folder)

    def test_get_pdbid_dir_emdb_set_first(self):
        final_output_folder = os.path.join(self.output_folder, self.pdbid_hash, self.pdbid)
        of = outputFiles(emdbID=self.emdbid, outputRoot=self.output_folder)
        of.set_pdb_id(entry_id=self.pdbid)
        ret = of.get_entry_output_folder()
        self.assertTrue(ret == final_output_folder)

    def test_set_accession_pdbid(self):
        of = outputFiles(pdbID=self.pdbid)
        ret = of.set_accession()
        self.assertTrue(ret == self.pdbid)

    def test_set_accession_emdbid(self):
        of = outputFiles(emdbID=self.emdbid)
        ret = of.set_accession()
        self.assertTrue(ret == self.emdb_accession)

    def test_set_accession_pdbid_and_not_set_emdbid(self):
        of = outputFiles(pdbID=self.pdbid, emdbID=self.emdbid)
        ret = of.set_accession()
        self.assertTrue(ret == self.pdbid)

    def test_set_accession_pdbid_and_emdbid(self):
        of = outputFiles(pdbID=self.pdbid, emdbID=self.emdbid)
        of.set_accession_variables(with_emdb=True)
        ret = of.set_accession()
        accession = '{}_{}'.format(self.emdb_accession, self.pdbid)
        self.assertTrue(ret == accession)

    def test_set_accession_pdbid_get_core_files(self):
        output_ret = {'xml': '/nfs/test/cb/1cbs/1cbs_validation.xml', 
                    'pdf': '/nfs/test/cb/1cbs/1cbs_validation.pdf', 
                    'full_pdf': '/nfs/test/cb/1cbs/1cbs_full_validation.pdf', 
                    'png': '/nfs/test/cb/1cbs/1cbs_multipercentile_validation.png', 
                     'svg': '/nfs/test/cb/1cbs/1cbs_multipercentile_validation.svg'}
        of = outputFiles(pdbID=self.pdbid, outputRoot=self.output_folder)
        of.set_accession()
        ret = of.get_core_validation_files()
        self.assertTrue(ret == output_ret)

    def test_set_accession_pdbid_get_map_files(self):
        output_ret = {'fofc': '/nfs/test/cb/1cbs/1cbs_validation_fo-fc_map_coef.cif', 
                     '2fofc': '/nfs/test/cb/1cbs/1cbs_validation_2fo-fc_map_coef.cif'}
        of = outputFiles(pdbID=self.pdbid, outputRoot=self.output_folder)
        of.set_accession()
        ret = of.get_extra_validation_files()
        self.assertTrue(ret == output_ret)

if __name__ == '__main__':
    unittest.main()
