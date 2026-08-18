import logging
import os
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

    def testInitialStateCreatesIdleStatus(self) -> None:
        v = ValDataStore(self.entry, self.sessiondir)
        self.assertFalse(v.isValidationRunning())
        d = v.getDictionary()
        self.assertEqual(d["status"], "idle")

        # Session file should now exist on disk
        fpath = os.path.join(self.sessiondir, "%s-session-store.pic" % self.entry)
        self.assertTrue(os.path.exists(fpath))

    def testExistingSessionPreservesRunningState(self) -> None:
        v1 = ValDataStore(self.entry, self.sessiondir)
        self.assertTrue(v1.setValidationRunning(True))

        # Reopening the same entry/session should not reset status to idle
        v2 = ValDataStore(self.entry, self.sessiondir)
        self.assertTrue(v2.isValidationRunning())

    def testDifferentEntriesAreIndependent(self) -> None:
        v1 = ValDataStore(self.entry, self.sessiondir)
        v2 = ValDataStore("9xyz", self.sessiondir)

        self.assertTrue(v1.setValidationRunning(True))
        self.assertFalse(v2.isValidationRunning())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
