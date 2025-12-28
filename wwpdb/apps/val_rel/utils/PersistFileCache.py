##
# File:  PersistsFileCache.py
# Date:  19-Nov-2020Sep-2012
#
# Updates:
#
##
"""
 Implements a local file object cache for basic operations

 Will also allow negative caching of files using a per directory admin file
"""
import os
import json
import logging

from oslo_concurrency import lockutils

from wwpdb.io.file.DataFile import DataFile

logger = logging.getLogger(__name__)


class PersistFileCache(object):
    def __init__(self, cache_dir="/tmp"):
        self.__cache_dir = cache_dir
        lockutils.set_defaults(self.__cache_dir)

    def __getcachedir(self, fpath):
        """Returns the internal cachedir for fpath"""
        if fpath is None:
            return None

        # Remove starting slash if present on filename
        if fpath[0] == "/":
            fpath = fpath[1:]

        if len(fpath) == 0:
            return None

        basedir = os.path.dirname(os.path.normpath(fpath))
        return os.path.join(self.__cache_dir, basedir)

    def __getcachefile(self, fpath):
        """Returns filepath of fpath in cache"""
        cd = self.__getcachedir(fpath)
        if cd is None:
            return None

        bname = os.path.basename(fpath)

        # In case there are any ../ etc
        cache_path = os.path.normpath(os.path.join(cd, bname))
        return cache_path

    @lockutils.synchronized("sessiondatastore.lock", external=True)
    def add_file(self, realfpath, fpath):
        """Adds the contents of realfpath to the cache as fpath.
           Overwrites if present.

           Returns True on success
        """

        cache_dir = self.__getcachedir(fpath)
        if not cache_dir:
            return False

        cache_file = self.__getcachefile(fpath)

        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

        df = DataFile(realfpath)
        df.copy(dstPath=cache_file)

        return True

    @lockutils.synchronized("sessiondatastore.lock", external=True)
    def get_file(self, fpath, realfpath, symlink=False):
        """Retrieves fpath from the cache and copies it to realfpath
           If fpath is not in cache, returns False, else True.

           Timestamp will be preserved
        """

        cache_file = self.__getcachefile(fpath)
        if cache_file is None:
            return False

        if not os.path.exists(cache_file):
            return False

        df = DataFile(cache_file)
        if symlink:
            # First time putting in cache - file might exists when trying to retrieve
            if os.path.exists(realfpath):
                os.unlink(realfpath)
            df.symLink(dstPath=realfpath)
        else:
            df.copy(dstPath=realfpath)
        return True

    @lockutils.synchronized("sessiondatastore.lock", external=True)
    def exists(self, fpath):
        """Returns True if fpath in cache, else False"""
        cache_file = self.__getcachefile(fpath)
        return os.path.exists(cache_file)

    def __getmissingfilepath(self, fpath):
        """Returns the file path for the missing file"""
        cache_dir = self.__getcachedir(fpath)
        return os.path.join(cache_dir, "missing.json")

    def __getmissinglist(self, fpath):
        """Retrieves the json data for missing files"""
        mpath = self.__getmissingfilepath(fpath)

        if os.path.exists(mpath):
            with open(mpath, "r") as fin:
                jdata = json.load(fin)
                return jdata
        return []

    def __writemissinglist(self, fpath, mlist):
        """Writes the json data for missing files"""
        mpath = self.__getmissingfilepath(fpath)

        with open(mpath, "w") as fout:
            json.dump(mlist, fout)
        return True

    @lockutils.synchronized("sessiondatastore.lock", external=True)
    def add_negative_cache(self, fpath):
        cache_dir = self.__getcachedir(fpath)

        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

        mlist = self.__getmissinglist(fpath)
        npath = os.path.normpath(fpath)
        if npath not in mlist:
            mlist.append(npath)
            ret = self.__writemissinglist(fpath, mlist)
        else:
            ret = True

        return ret

    @lockutils.synchronized("sessiondatastore.lock", external=True)
    def is_negative_cache(self, fpath):
        mlist = self.__getmissinglist(fpath)

        npath = os.path.normpath(fpath)
        if npath in mlist:
            return True
        return False

    @lockutils.synchronized("sessiondatastore.lock", external=True)
    def cache_file_status(self, fpath):
        """Returns one of three statuses for fpath
        True if have a file
        False if negative cache
        None - cache does not know about file.
        """

        cache_file = self.__getcachefile(fpath)
        # Cannot make a name of the file
        if cache_file is None:
            return None

        # If file in cache
        if os.path.exists(cache_file):
            return True

        # Check negative cache
        mlist = self.__getmissinglist(fpath)
        npath = os.path.normpath(fpath)
        if npath in mlist:
            return False

        # We known nothing
        return None
