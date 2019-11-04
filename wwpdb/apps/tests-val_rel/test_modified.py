import unittest
import logging
import os
import tempfile
import shutil
from wwpdb.apps.val_rel.ValidateRelease import runValidation

def touch(fname, times=None):
    with open(fname, 'a'):
        os.utime(fname, times)

class ModifiedFolderTests(unittest.TestCase):

    def setUp(self):
        self.output_dir = tempfile.mkdtemp
        self.input_dir = tempfile.mkdtemp
        self.pdbid = '1cbs'
        self.emdb = 'EMD-1234'
        self.pdbid_file = os.path.join(self.input_dir, self.pdbid + '.cif')
        self.emdb_file = os.path.join(self.input_dir, self.emdb + '.xml')
        self.rv = runValidation()
        self.rv.entry_output_folder = self.output_dir

    def tearDown(self):
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir, ignore_errors=True)
        if os.path.exists(self.input_dir):
            shutil.rmtree(self.input_dir, ignore_errors=True)

    def test_always_run(self):
        self.rv.always_recalculate = True
        ret = self.rv.check_modified()
        self.assertTrue(ret)

    def test_pdb_modified(self):
        self.rv.pdbid = self.pdbid
        self.rv.modelPath = self.pdbid_file
        touch(self.pdbid_file)
        ret = self.rv.check_modified()
        self.assertTrue(ret)

    def test_emdb_modified(self):
        self.rv.emdbid = self.emdb
        self.rv.emXmlPath = self.emdb_file
        touch(self.emdb_file)
        ret = self.rv.check_modified()
        self.assertTrue(ret)

    def test_pdb_folder_modified(self):
        pass




if __name__ == '__main__':
    unittest.main()
