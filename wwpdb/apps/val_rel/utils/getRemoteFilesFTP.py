import os
import time
import datetime
import ftplib
import logging
import shutil
import tempfile

logger = logging.getLogger(__name__)


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
    def __init__(self, server, output_path):
        self.output_path = output_path
        self.ftp = ftplib.FTP(server)
        self.ftp.login()
        self.setup_output_path()
        # logger.debug("Setup for %s to %s", server, output_path)

    def setup_output_path(self):
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

    def setup_output_directory(self, directory):
        self.output_path = os.path.join(self.output_path, directory)
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

    def get_file(self, remote_file):
        file_name = os.path.join(self.output_path, remote_file)
        logger.debug("Transferring file %s to %s", remote_file, file_name)
        with open(file_name, 'wb') as out_file:
            self.ftp.retrbinary("RETR " + remote_file, out_file.write)
        # logger.debug("Output exists? %s", os.path.exists(file_name))
        # See if can get details..
        mtime = self.get_remote_file_mtime(remote_file)
        if mtime is not None:
            logger.debug("Setting mtime on %s to %s", file_name, mtime)
            os.utime(file_name, (mtime, mtime))
            


    def get_remote_file_mtime(self, remote_file):
        # Try to retrieve remote file time from server.
        # Returns None if could not be determined

        # See https://stackoverflow.com/questions/29026709/how-to-get-ftp-files-modify-time-using-python-ftplib
        # Python 3 has added mlsd which could be used - but we are not there yet

        # Several attempts to see if server supports one. Raises exception if command not know
        ts = None
        try:
            # MDTM is supported by all wwpdb partner ftp sites
            mdtmr = self.ftp.voidcmd("MDTM %s" % remote_file)
            # Make sure get 213 return
            if mdtmr[0:3] != "213":
                return None
            ts = mdtmr[4:].strip()

            # Fall through

        except Exception as e:
            try:
                # Fall back on MLST - which is more machine readable - but less universal

                mlst = self.ftp.voidcmd("MLST %s" % remote_file)

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
        size = 0
        try:
            size = self.ftp.size(remote_file)
        except:
            size = None
        return size

    def is_file(self, remote_file):
        if self.get_size(remote_file):
            return True
        return False

    def change_ftp_directory(self, directory):
        if directory:
            try:
                self.ftp.cwd(directory)
                return True
            except Exception as e:
                logger.error(e)
        return False

    def get_url(self, directory=None, filename=None):
        """Retrieves files from directory.  Returns list of files retrieved"""
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
            files = self.ftp.nlst()
        for filename in files:
            if self.is_file(filename):
                self.get_file(filename)
                ret_files.append(filename)
        return ret_files

    def get_directory(self, directory):
        ok = self.change_ftp_directory(directory)
        if not ok:
            return False
        objects = self.ftp.nlst()
        if objects:
            for obj in objects:
                if self.is_file(obj):
                    self.get_file(obj)
                else:
                    logging.debug('not a file: {}'.format(obj))
                    self.setup_output_directory(obj)
                    self.get_directory(obj)
                    self.ftp.cwd('..')
                    self.output_path = os.path.join(self.output_path, '..')
            return True
        return False
