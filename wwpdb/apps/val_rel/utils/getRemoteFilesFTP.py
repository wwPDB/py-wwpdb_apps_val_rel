import ftplib
import logging
import os

logger = logging.getLogger(__name__)


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
