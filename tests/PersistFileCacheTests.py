import os
import shutil
import unittest

if __package__ is None or __package__ == "":
    import sys
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import TESTOUTPUT  # type: ignore[import-not-found]  # pylint: disable=import-error
else:
    from .commonsetup import (  # noqa: TID252  # pragma: no cover
        TESTOUTPUT,
    )

from wwpdb.apps.val_rel.utils.PersistFileCache import PersistFileCache


class PersisFileCacheTests(unittest.TestCase):
    init_once = False

    def setUp(self) -> None:
        self.__cache = os.path.join(TESTOUTPUT, "cache")
        self.__tmpdir = os.path.join(TESTOUTPUT, "persist_data")
        if not self.init_once:
            shutil.rmtree(self.__cache, ignore_errors=True)
            shutil.rmtree(self.__tmpdir, ignore_errors=True)
            self.init_once = True

    def testFileAccess(self) -> None:
        """Test adding and access to file"""

        pfc = PersistFileCache(self.__cache)
        lfile = __file__
        cfname = os.path.join(self.__tmpdir, "somewhere/file.txt")

        ret = pfc.add_file(lfile, cfname)
        self.assertTrue(ret, "Adding file failed")

        self.assertTrue(pfc.exists(cfname))

        outfile = os.path.join(self.__tmpdir, "testout.txt")
        self.assertTrue(pfc.exists(cfname))

        self.assertTrue(pfc.get_file(cfname, outfile))

        self.assertTrue(os.path.exists(outfile))

        self.assertTrue(abs(os.path.getmtime(outfile) - os.path.getmtime(lfile)) < 1)

    def testNegativeCache(self) -> None:
        """Test adding to negative cache"""

        pfc = PersistFileCache(self.__cache)
        cfname = os.path.join(self.__tmpdir, "somewhereelse/file.txt-negative")

        self.assertTrue(pfc.add_negative_cache(cfname))

        self.assertTrue(pfc.is_negative_cache(cfname))

        # Adding again should be ok
        self.assertTrue(pfc.add_negative_cache(cfname))

    def testCacheFileStatus(self) -> None:
        """Test testing fail status"""

        pfc = PersistFileCache(self.__cache)
        lfile = __file__
        cfname = os.path.join(self.__tmpdir, "somewherenew/file.txt")
        cfname2 = os.path.join(self.__tmpdir, "somewhereelse/file.txt")
        cfname3 = os.path.join(self.__tmpdir, "somewhereelse/file.txt.new")

        ret = pfc.add_file(lfile, cfname)
        self.assertTrue(ret, "Adding file failed")

        self.assertTrue(pfc.add_negative_cache(cfname2))

        self.assertEqual(pfc.cache_file_status(cfname), True)
        self.assertEqual(pfc.cache_file_status(cfname2), False)
        self.assertEqual(pfc.cache_file_status(cfname3), None)

    def testFileSymlink(self) -> None:
        """Test adding and symlink to file"""

        pfc = PersistFileCache(self.__cache)
        lfile = __file__
        cfname = os.path.join(self.__tmpdir, "somewhere/file.txt")

        ret = pfc.add_file(lfile, cfname)
        self.assertTrue(ret, "Adding file failed")

        self.assertTrue(pfc.exists(cfname))

        outfile = os.path.join(self.__tmpdir, "testout.txt2")
        self.assertTrue(pfc.exists(cfname))

        self.assertTrue(pfc.get_file(cfname, outfile, symlink=True))

        self.assertTrue(os.path.exists(outfile))

        self.assertTrue(abs(os.path.getmtime(outfile) - os.path.getmtime(lfile)) < 1)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
