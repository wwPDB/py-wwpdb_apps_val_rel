import unittest
import logging
import os
import tempfile
import shutil
from wwpdb.apps.val_rel.ValidateRelease import runValidation

def touch(fname, times=None):
    with open(fname, 'a'):
        os.utime(fname, times)

class OuputFolderTests(unittest.TestCase):

    def setUp(self):
        self.pdbid = '1cbs'
        self.emdb = 'EMD-1234'
        self.output_folder = '/nfs/test'
        self.rv = runValidation()

    def test_pdbid(self):
        self.rv.pdbid = self.pdbid
        self.rv.outputRoot = self.output_folder
        self.rv.set_output_dir_and_files()
        print(self.rv.entry_output_folder)