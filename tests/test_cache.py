
import unittest
import os

from wwpdb.apps.val_rel.utils.PersistFileCache import PersistFileCache


class PersisFileCacheTests(unittest.TestCase):
    def setUp(self):
        self.__cache = "/tmp/cache"

    def testFileAccess(self):
        """Test adding and access to file"""

        pfc = PersistFileCache(self.__cache)
        lfile = __file__
        cfname = "/tmp/somewhere/file.txt"

        ret = pfc.add_file(lfile, cfname)
        self.assertTrue(ret, "Adding file failed")

        self.assertTrue(pfc.exists(cfname))

        outfile = "/tmp/testout.txt"
        self.assertTrue(pfc.exists(cfname))

        self.assertTrue(pfc.get_file(cfname, outfile))

        self.assertTrue(os.path.exists(outfile))

        self.assertTrue(abs(os.path.getmtime(outfile) - os.path.getmtime(lfile)) < 1)

    def testNegativeCache(self):
        """Test adding to negative cache"""

        pfc = PersistFileCache(self.__cache)
        cfname = "/tmp/somewhereelse/file.txt-negative"

        self.assertTrue(pfc.add_negative_cache(cfname))

        self.assertTrue(pfc.is_negative_cache(cfname))

        # Adding again should be ok
        self.assertTrue(pfc.add_negative_cache(cfname))

    def testCacheFileStatus(self):
        """Test testing fail status"""

        pfc = PersistFileCache(self.__cache)
        lfile = __file__
        cfname = "/tmp/somewherenew/file.txt"
        cfname2 = "/tmp/somewhereelse/file.txt"
        cfname3 = "/tmp/somewhereelse/file.txt.new"

        ret = pfc.add_file(lfile, cfname)
        self.assertTrue(ret, "Adding file failed")

        self.assertTrue(pfc.add_negative_cache(cfname2))

        self.assertEqual(pfc.cache_file_status(cfname), True)
        self.assertEqual(pfc.cache_file_status(cfname2), False)
        self.assertEqual(pfc.cache_file_status(cfname3), None)

    def testFileSymlink(self):
        """Test adding and symlink to file"""

        pfc = PersistFileCache(self.__cache)
        lfile = __file__
        cfname = "/tmp/somewhere/file.txt"

        ret = pfc.add_file(lfile, cfname)
        self.assertTrue(ret, "Adding file failed")

        self.assertTrue(pfc.exists(cfname))

        outfile = "/tmp/testout.txt2"
        self.assertTrue(pfc.exists(cfname))

        self.assertTrue(pfc.get_file(cfname, outfile, symlink=True))

        self.assertTrue(os.path.exists(outfile))

        self.assertTrue(abs(os.path.getmtime(outfile) - os.path.getmtime(lfile)) < 1)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
