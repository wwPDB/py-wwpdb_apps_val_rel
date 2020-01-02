import unittest
import os
from wwpdb.apps.val_rel.ValidateRelease import runValidation


def touch(fname, times=None):
    with open(fname, "a"):
        os.utime(fname, times)


class OuputFolderTests(unittest.TestCase):
    def setUp(self):
        self.pdbid = "1cbs"
        self.pdbid_hash = self.pdbid[1:3]
        self.emdb = "EMD-1234"
        self.output_folder = "/nfs/test"
        self.rv = runValidation()

    def test_pdbid(self):
        output_dir = os.path.join(self.output_folder, self.pdbid_hash, self.pdbid)
        self.rv.pdbid = self.pdbid
        self.rv.outputRoot = self.output_folder
        self.rv.set_output_dir_and_files()
        self.assertTrue(self.rv.entry_output_folder == output_dir)

    def test_emdbid(self):
        output_dir = os.path.join(self.output_folder, self.emdb)
        self.rv.emdbid = self.emdb
        self.rv.outputRoot = self.output_folder
        self.rv.set_output_dir_and_files()
        self.assertTrue(self.rv.entry_output_folder == output_dir)

    def test_pdbid_and_emdbid(self):
        output_dir = os.path.join(self.output_folder, self.pdbid_hash, self.pdbid)
        self.rv.pdbid = self.pdbid
        self.rv.emdbid = self.emdb
        self.rv.outputRoot = self.output_folder
        self.rv.set_output_dir_and_files()
        self.assertTrue(self.rv.entry_output_folder == output_dir)


if __name__ == "__main__":
    unittest.main()
