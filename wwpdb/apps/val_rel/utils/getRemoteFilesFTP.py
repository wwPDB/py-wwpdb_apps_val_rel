import ftplib
import logging
import os
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


def remove_local_temp_ftp(temp_dir):
    if temp_dir:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)


class GetRemoteFiles:

    def __init__(self, server, output_path):
        self.output_path = output_path
        self.ftp = ftplib.FTP(server)
        self.ftp.login()
        self.setup_output_path()

    def setup_output_path(self):
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

    def setup_output_directory(self, directory):
        self.output_path = os.path.join(self.output_path, directory)
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

    def get_file(self, remote_file):
        file_name = os.path.join(self.output_path, remote_file)
        with open(file_name, 'wb') as out_file:
            self.ftp.retrbinary("RETR " + remote_file, out_file.write)

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
        ret_files = []
        if directory:
            ok = self.change_ftp_directory(directory)
            if not ok:
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
