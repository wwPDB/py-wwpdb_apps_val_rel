import ftplib
import os


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

    def get_url(self, directory=None, filename=None):
        if directory:
            self.ftp.cwd(directory)
        if filename:
            files = [filename]
        else:
            files = self.ftp.nlst()
        for filename in files:
            if self.is_file(filename):
                self.get_file(filename)
        return files

    def get_directory(self, directory):
        self.ftp.cwd(directory)
        objects = self.ftp.nlst()
        print(objects)
        for obj in objects:
            if self.is_file(obj):
                self.get_file(obj)
            else:
                print('not a file: {}'.format(obj))
                self.setup_output_directory(obj)
                self.get_directory(obj)
                self.ftp.cwd('..')
                self.output_path = os.path.join(self.output_path, '..')
