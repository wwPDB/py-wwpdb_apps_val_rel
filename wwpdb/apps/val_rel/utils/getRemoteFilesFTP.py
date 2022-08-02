import datetime
import ftplib
import logging
import os
import shutil
import tempfile
import time

logger = logging.getLogger(__name__)

from wwpdb.apps.val_rel.utils.PersistFileCache import PersistFileCache

def setup_local_temp_ftp(temp_dir, suffix, session_path):
    if not temp_dir:
        if not os.path.exists(session_path):
            os.makedirs(session_path)
        temp_dir = tempfile.mkdtemp(
            dir=session_path,
            prefix="ftp_{}_".format(suffix)
        )
    return temp_dir


def remove_local_temp_ftp(temp_dir, require_empty=False):
    """Removes the temporary directory. If require_empty true, will skip if not"""
    if temp_dir and os.path.exists(temp_dir):
        if require_empty:
            dlist = os.listdir(temp_dir)
            if len(dlist) > 0:
                logger.debug("Skipping removal of %s as not empty" % temp_dir)
                return
        shutil.rmtree(temp_dir, ignore_errors=True)


class GetRemoteFiles(object):
    def __init__(self, server, cache=None):

        # Single underscore for __del__ to be able to find
        self._ftp = self.__connect(server)
        # logger.info("Connect!!! %s", self._ftp)
        self._ftp.login()
        self.__cache = cache
        # The current remote directory as we go up and down tree
        self.__curdir = "." 
        # logger.debug("Setup for %s to %s", server, output_path)
    
    def __del__(self):
        # for cases where ftplib.FTP.__init__() failed
        if hasattr(self, '_ftp'):
            # possible exceptions in ftp.quit() will be ignored
            self.disconnect()

    def __connect(self, server):
        """Connects to remote server with retry"""
        
        retry = 0
        sleep = 2
        ftp = None

        while 1:
            try:
                ftp = ftplib.FTP(server)
                return ftp
            except ftplib.error_temp as e:
                ecode = str(e)[:3]
                if ecode == "421":
                    if retry > 7:
                        raise
                    logger.error("Remote resource unavailable - sleep %s and retry %s", sleep, str(e))
                    time.sleep(sleep)
                    retry += 1
                    sleep *= 2
                    continue
            # unhandled exception not caught - raises us
        # Never reached
        
    def _check_connection(self):
        retries = 3
        
        while retries > 0:
            try:
                return self._ftp.voidcmd("noop")
            except Exception as e:
                logger.error(e)
                retries -= 1
                self._ftp.login()
        
        raise Exception("error connecting to server")

    def _setup_output_path(self, output_path):
        if not os.path.exists(output_path):
            os.makedirs(output_path)

    def get_file(self, remote_file, output_path):
        self._check_connection()
        self._setup_output_path(output_path)

        file_name = os.path.join(output_path, remote_file)
        logger.debug("Transferring file %s to %s", remote_file, file_name)
        # logger.debug("Cache is %s", self.__cache)
        if self.__cache is not None:
            # See if in cache
            pfc = PersistFileCache(self.__cache)
            rp = os.path.join(self.__curdir, remote_file)
            if pfc.exists(rp):
                pfc.get_file(rp, file_name, symlink=True)
                logger.debug("Found %s in cache", rp)
                return
            # logger.debug("Did not find %s in cache", remote_file)

        with open(file_name, 'wb') as out_file:
            self._ftp.retrbinary("RETR " + remote_file, out_file.write)
            
        # File always exist - but might be zero length.... Annoying interface
        #logger.debug("Output exists? %s", os.path.exists(file_name))
        # See if can get details..
        mtime = self.get_remote_file_mtime(remote_file)
        if mtime is not None:
            logger.debug("Setting mtime on %s to %s", file_name, mtime)
            os.utime(file_name, (mtime, mtime))
        if self.__cache is not None:
            pfc.add_file(file_name, rp)
            #logger.debug("Adding %s to cache", rp)

    def get_remote_file_mtime(self, remote_file):
        self._check_connection()
        # Try to retrieve remote file time from server.
        # Returns None if could not be determined

        # See https://stackoverflow.com/questions/29026709/how-to-get-ftp-files-modify-time-using-python-ftplib
        # Python 3 has added mlsd which could be used - but we are not there yet

        # Several attempts to see if server supports one. Raises exception if command not know
        ts = None
        try:
            # MDTM is supported by all wwpdb partner ftp sites
            mdtmr = self._ftp.voidcmd("MDTM %s" % remote_file)
            # Make sure get 213 return
            if mdtmr[0:3] != "213":
                return None
            ts = mdtmr[4:].strip()

            # Fall through

        except Exception as e:
            try:
                # Fall back on MLST - which is more machine readable - but less universal

                mlst = self._ftp.voidcmd("MLST %s" % remote_file)

                if not mlst:
                    return None
                for line in mlst.split('\n'):
                    if line[0:3] == '250':
                        continue
                    l = line.strip()
                    facts_found, _, fname = l.partition(" ")
                    factsd = {}
                    # Last ends in semicolor
                    for fact in facts_found[:-1].split(";"):
                        key, _dum, value = fact.partition("=")
                        factsd[key.lower()] = value
                ts = factsd.get('modify', None)
                # None caught below

            except Exception as e:
                return None

        # print("TS: %s" % ts)
        if not ts:
            return None

        try:
            # Parse string like 0200704134000  -- 14 digits ["." 1*digit]
            # Could have optional tenths of second after period
            bts = ts.split(".")[0]
            dt = datetime.datetime.strptime(bts, "%Y%m%d%H%M%S")
            time_tuple = dt.timetuple()
            timestamp = time.mktime(time_tuple)
            return timestamp
        except:
            return None

    def get_size(self, remote_file):
        self._check_connection()

        size = 0
        try:
            size = self._ftp.size(remote_file)
        except:
            size = None
        return size

    def is_file(self, remote_file):
        self._check_connection()

        if self.get_size(remote_file):
            return True
        return False

    def change_ftp_directory(self, directory):
        self._check_connection()

        logger.debug("Changing directory %s", directory)
        if directory:
            try:
                self._ftp.cwd(directory)
                if directory[0] == '/':
                    self.__curdir = directory
                else:
                    self.__curdir = os.path.join(self.__curdir, directory)
                logger.debug("cur directory is %s", self.__curdir)
                return True
            except Exception as e:
                logger.error(e)
        return False

    def get_url(self, output_path, directory=None, filename=None):
        """Retrieves files from directory.  Returns list of files retrieved"""
        self._check_connection()

        ret_files = []
        # logger.debug("Directory %s, filename %s", directory, filename)
        if directory:
            ok = self.change_ftp_directory(directory)
            if not ok:
                logger.error("Failed to change directory to %s", directory)
                return []
        if filename:
            files = [filename]
        else:
            files = self._ftp.nlst()
        for filename in files:
            if self.is_file(filename):
                self.get_file(filename, output_path)
                ret_files.append(filename)
        return ret_files

    def get_directory(self, directory, output_path):
        """Recursivle retrieve contents of directory"""
        self._check_connection()
        
        # Improvement - cache nlst?
        ok = self.change_ftp_directory(directory)
        if not ok:
            return False
        objects = self._ftp.nlst()
        if objects:
            for obj in objects:
                if self.is_file(obj):
                    self.get_file(obj, output_path)
                else:
                    logging.debug('not a file: {}'.format(obj))
                    # Skip recursion
                    if obj == "." or obj == "..":
                        continue

                    output_path = os.path.join(output_path, obj)
                    self._setup_output_path(output_path)
                    self.get_directory(obj, output_path)

                    self._ftp.cwd('..')
                    output_path = os.path.join(output_path, '..')
                    self.__curdir = os.path.join(self.__curdir, "..")
                    logger.debug("curr directory %s", self.__curdir)
            return True
        return False

    def disconnect(self):
        """Issues 'QUIT' command to server

        Note: `quit()` may also raise an exception (see [1])
        It will be ignored by __del__ even if not wrapped by try/except (see [2]), so try/except
        is necessary for when disconnect() is called directly, as to set self._ftp to None

        [1] https://docs.python.org/3.9/library/ftplib.html#ftplib.FTP.quit
        [2] https://docs.python.org/3/reference/datamodel.html#object.__del__
        """
        if self._ftp is not None:
            # logger.info("Disconnect %s", self._ftp)
            try:
                self._ftp.quit()
            except:
                logger.error("Error trying to close ftp connection")

            self._ftp = None
