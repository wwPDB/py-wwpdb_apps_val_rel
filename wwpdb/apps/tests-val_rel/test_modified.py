import unittest
import os
import tempfile
import shutil
import time
from wwpdb.apps.val_rel.ValidateRelease import runValidation


def touch(fname, times=None):
    with open(fname, "a"):
        os.utime(fname, times)


class ModifiedFolderTests(unittest.TestCase):
    def setUp(self):
        self.input_dir = tempfile.mkdtemp()
        self.pdbid = "1cbs"
        self.pdbid_hash = self.pdbid[1:3]
        self.emdb = "EMD-1234"
        self.pdbid_file = os.path.join(self.input_dir, self.pdbid + ".cif")
        self.emdb_file = os.path.join(self.input_dir, self.emdb + ".xml")
        touch(self.pdbid_file)
        touch(self.emdb_file)
        self.output_dir = tempfile.mkdtemp()
        self.pdb_output_folder = os.path.join(
            self.output_dir, 'pdb', self.pdbid_hash, self.pdbid
        )
        self.emdb_output_folder = os.path.join(self.output_dir, 'emd', self.emdb, 'validation')
        self.rv = runValidation()
        self.rv.setOutputRoot(self.output_dir)
        time.sleep(1)
        os.makedirs(self.pdb_output_folder)
        os.makedirs(self.emdb_output_folder)

    def tearDown(self):
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir, ignore_errors=True)
        if os.path.exists(self.input_dir):
            shutil.rmtree(self.input_dir, ignore_errors=True)

    def test_always_run(self):
        self.rv.setPdbId(self.pdbid)
        self.rv.setAlwaysRecalculate(True)
        ret = self.rv.check_modified()
        # expected True - is modified - run validation
        self.assertTrue(ret)

    def test_pdb_not_modified(self):
        self.rv.setPdbId(self.pdbid)
        self.rv.setModelPath(self.pdbid_file)
        ret = self.rv.check_modified()
        # expected False - not modified - don't run validation
        self.assertFalse(ret)

    def test_emdb_not_modified(self):
        self.rv.setEmdbId(self.emdb)
        self.rv.setEmXmlPath(self.emdb_file)
        ret = self.rv.check_modified()
        # expected False - not modified - don't run validation
        self.assertFalse(ret)

    def test_pdb_modified(self):
        self.rv.setPdbId(self.pdbid)
        self.rv.setModelPath(self.pdbid_file)
        touch(self.pdbid_file)
        ret = self.rv.check_modified()
        # expected True - modified - do run validation
        self.assertTrue(ret)

    def test_emdb_modified(self):
        self.rv.setEmdbId(self.emdb)
        self.rv.setEmXmlPath(self.emdb_file)
        touch(self.emdb_file)
        ret = self.rv.check_modified()
        # expected True - modified - do run validation
        self.assertTrue(ret)

    def test_pdb_and_emdb_with_pdb_modified(self):
        self.rv.setPdbId(self.pdbid)
        self.rv.setEmdbId(self.emdb)
        self.rv.setModelPath(self.pdbid_file)
        touch(self.pdbid_file)
        ret = self.rv.check_modified()
        # expected True - modified - do run validation
        self.assertTrue(ret)

    def test_pdb_and_emdb_with_emdb_modified(self):
        self.rv.setPdbId(self.pdbid)
        self.rv.setEmdbId(self.emdb)
        self.rv.setModelPath(self.pdbid_file)
        self.rv.setEmXmlPath(self.emdb_file)
        touch(self.emdb_file)
        ret = self.rv.check_modified()
        # expected True - modified - do run validation
        self.assertTrue(ret)

    def test_pdb_folder_modified(self):
        self.rv.setPdbId(self.pdbid)
        self.rv.setModelPath(self.pdbid_file)
        touch(self.pdbid_file)
        shutil.rmtree(self.pdb_output_folder)
        time.sleep(1)
        os.makedirs(self.pdb_output_folder)
        ret = self.rv.check_modified()
        # expected False - not modified - don't run validation
        self.assertFalse(ret)


if __name__ == "__main__":
    unittest.main()
