import unittest
import logging
import os
from wwpdb.apps.val_rel import outputFiles


class OutputFilesTests(unittest.TestCase):

    def __init__(self):
        pass

    def test_get_pdbid_dir(self):
        pdbid = '1cbs'
        output_folder = os.path.join('nfs', 'test')
        of = outputFiles(pdbID=pdbid, output_folder=output_folder)
        ret = of.get_entry_output_folder()
        print(ret)

if __name__ == '__main__':
    unittest.main()
