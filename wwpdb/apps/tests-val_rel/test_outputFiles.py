import unittest
import logging
import os
from wwpdb.apps.val_rel.outputFiles import outputFiles


class OutputFilesTests(unittest.TestCase):

    def setUp(self):
        pass

    def test_get_pdbid_dir(self):
        pdbid = '1cbs'
        pdb_hash = pdbid[1:3]
        output_folder = os.path.join(os.sep, 'nfs', 'test')
        final_output_folder = os.path.join(output_folder, pdb_hash, pdbid)
        of = outputFiles(pdbID=pdbid, outputRoot=output_folder)
        ret = of.get_entry_output_folder()
        self.assertTrue(ret == final_output_folder)

    def test_get_emdb_dir(self):
        emdbid = 'EMD-1234'
        output_folder = os.path.join(os.sep, 'nfs', 'test')
        final_output_folder = os.path.join(output_folder, 'emd', emdbid, 'validation')
        of = outputFiles(emdbID=emdbid, outputRoot=output_folder)
        ret = of.get_entry_output_folder()
        self.assertTrue(ret == final_output_folder)

    def test_get_pdbid_and_emdb_dir(self):
        pdbid = '1cbs'
        emdbid = 'EMD-1234'
        pdb_hash = pdbid[1:3]
        output_folder = os.path.join(os.sep, 'nfs', 'test')
        final_output_folder = os.path.join(output_folder, pdb_hash, pdbid)
        of = outputFiles(pdbID=pdbid, outputRoot=output_folder)
        ret = of.get_entry_output_folder()
        self.assertTrue(ret == final_output_folder)

if __name__ == '__main__':
    unittest.main()
