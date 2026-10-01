import logging
import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, call, patch

from wwpdb.apps.val_rel.utils.ValDataStore import ValDataStore

logger = logging.getLogger()

MODULE = "wwpdb.apps.val_rel.utils.ValDataStore"


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

    def testEnsureSessionDirCreatesMissingDir(self) -> None:
        v = ValDataStore(self.entry, self.sessiondir)
        shutil.rmtree(self.sessiondir)
        ensure = v._ensureSessionDir  # noqa: SLF001  pylint: disable=protected-access
        with patch.object(v, "_ensureSessionDir", wraps=ensure) as mockEnsure, patch(
            MODULE + ".os.makedirs", wraps=os.makedirs
        ) as mockMakedirs:
            self.assertTrue(v.setValidationRunning(True))
        mockEnsure.assert_called_once_with()
        # oslo_concurrency file locking in ServiceDataStore may also call os.makedirs for its lock directory
        self.assertEqual(mockMakedirs.call_args_list.count(call(self.sessiondir, exist_ok=True)), 1)
        self.assertTrue(os.path.isdir(self.sessiondir))

    def testEnsureSessionDirSkipsExistingDir(self) -> None:
        v = ValDataStore(self.entry, self.sessiondir)
        ensure = v._ensureSessionDir  # noqa: SLF001  pylint: disable=protected-access
        with patch.object(v, "_ensureSessionDir", wraps=ensure) as mockEnsure, patch(
            MODULE + ".os.makedirs", wraps=os.makedirs
        ) as mockMakedirs:
            self.assertFalse(v.isValidationRunning())
        mockEnsure.assert_called_once_with()
        # oslo_concurrency file locking in ServiceDataStore may also call os.makedirs for its lock directory
        self.assertNotIn(self.sessiondir, [c.args[0] for c in mockMakedirs.call_args_list])

    def testStatusMethodsEnsureSessionDir(self) -> None:
        v = ValDataStore(self.entry, self.sessiondir)
        mockEnsure = MagicMock()
        with patch.object(v, "_ensureSessionDir", mockEnsure):
            v.isValidationRunning()
            self.assertEqual(mockEnsure.call_count, 1)
            v.setValidationRunning(True)
            self.assertEqual(mockEnsure.call_count, 2)

    def testSessionDirRecreatedAfterRemoval(self) -> None:
        v = ValDataStore(self.entry, self.sessiondir)
        shutil.rmtree(self.sessiondir)
        self.assertFalse(os.path.isdir(self.sessiondir))
        self.assertTrue(v.setValidationRunning(True))
        self.assertTrue(os.path.isdir(self.sessiondir))
        self.assertTrue(v.isValidationRunning())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
