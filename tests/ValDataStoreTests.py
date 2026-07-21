import logging
import shutil
import tempfile
import unittest

from wwpdb.apps.val_rel.utils.ValDataStore import ValDataStore

logger = logging.getLogger()


class ValDataStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sessiondir = tempfile.mkdtemp()
        self.entry = "1abc"

    def tearDown(self) -> None:
        shutil.rmtree(self.sessiondir)

    def testStore(self) -> None:
        v = ValDataStore(self.entry, self.sessiondir)
        self.assertFalse(v.isValidationRunning())
        self.assertTrue(v.setValidationRunning(True))
        self.assertTrue(v.isValidationRunning())
        self.assertTrue(v.setValidationRunning(False))
        self.assertFalse(v.isValidationRunning())
        d = v.getDictionary()
        self.assertTrue(d["status"] == "idle")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
