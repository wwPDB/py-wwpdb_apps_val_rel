import unittest
import tempfile
import logging

from wwpdb.apps.val_rel.utils.ValDataStore import ValDataStore

FORMAT = "%(funcName)s (%(levelname)s) - %(message)s"
logging.basicConfig(format=FORMAT)
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class ValDataStoreTests(unittest.TestCase):
    def setUp(self):
        self.sessiondir = tempfile.mkdtemp()
        self.entry = '1abc'

    def testStore(self):
        v = ValDataStore(self.entry, self.sessiondir)
        self.assertFalse(v.isValidationRunning())
        self.assertTrue(v.setValidationRunning(True))
        self.assertTrue(v.isValidationRunning())
        self.assertTrue(v.setValidationRunning(False))
        self.assertFalse(v.isValidationRunning())


if __name__ == "__main__":
    unittest.main()
