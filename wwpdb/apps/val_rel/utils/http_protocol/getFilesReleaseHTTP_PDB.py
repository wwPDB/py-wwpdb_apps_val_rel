import os
import logging
from wwpdb.utils.config.ConfigInfo import getSiteId
from wwpdb.io.locator.ReleaseFileNames import ReleaseFileNames
from wwpdb.io.locator.localFTPPathInfo import LocalFTPPathInfo
from wwpdb.apps.val_rel.config.ValConfig import ValConfig
from wwpdb.apps.val_rel.utils.http_protocol.getRemoteFilesHTTP import GetRemoteFiles, setup_local_temp_ftp, remove_local_temp_ftp

logger = logging.getLogger(__name__)


class getFilesReleaseHttpPDB(object):
    def __init__(self, pdbid, site_id=getSiteId(), cache=None):
        self.__site_id = site_id
        self.__cache = cache
        self.__rf = ReleaseFileNames()
        self.__local_ftp = LocalFTPPathInfo()
        self.__temp_local_ftp = None
        vc = ValConfig(self.__site_id)
        self.server = vc.http_server
        self.session_path = vc.session_path
        self.ftp_prefix = vc.http_prefix
        protocol = vc.val_rel_protocol
        self.url_prefix = "%s://%s%s" % (protocol, self.server,self.ftp_prefix)
        self.__remote_ftp = LocalFTPPathInfo()
        self.__remote_ftp.set_ftp_pdb_root(self.url_prefix)
        self.url_prefix = self.__remote_ftp.get_ftp_pdb()
        self.pdb_id = pdbid
        self.__local_ftp_path = None
        self.grf = None

        if not self.__local_ftp.get_ftp_pdb():
            self.grf = GetRemoteFiles(server=self.server, cache=self.__cache)

    def get_model(self):
        """
        get the PDB model file - from OneDep then local FTP and then the remote FTP
        :return: file name if present or None
        """
        if not self.__local_ftp.get_ftp_pdb():
            url = self.__remote_ftp.get_model_fname(self.pdb_id)
            zip_file_name = ReleaseFileNames().get_model(accession=self.pdb_id, for_release=False)
            temp_file_path = self.get_remote_ftp_file(url=url, filename=zip_file_name)
        else:
            file_path = self.__local_ftp.get_model_fname(accession=self.pdb_id)
            logger.debug('checking local model filepath: {}'.format(file_path))
            return self.check_filename(file_path)
        logger.debug('final model filepath: {}'.format(temp_file_path))
        return temp_file_path

    def get_sf(self):
        """
        get the PDB structure factor file - from OneDep then local FTP and then the remote FTP
        :return: file name if present or None
        """
        if not self.__local_ftp.get_ftp_pdb():
            url = self.__remote_ftp.get_structure_factors_fname(self.pdb_id)
            zip_file_name = ReleaseFileNames().get_structure_factor(accession=self.pdb_id, for_release=False)
            temp_file_path = self.get_remote_ftp_file(url=url, filename=zip_file_name)
        else:
            file_path = self.__local_ftp.get_structure_factors_fname(accession=self.pdb_id)
            logger.debug('checking local structure factor filepath: {}'.format(file_path))
            return self.check_filename(file_path)
        logger.debug('final structure factor filepath: {}'.format(temp_file_path))
        return temp_file_path

    def get_cs(self):
        """
        get the PDB chemical shift file - from OneDep then local FTP and then the remote FTP
        :return: file name if present or None
        """
        if not self.__local_ftp.get_ftp_pdb():
            url = self.__remote_ftp.get_chemical_shifts_fname(self.pdb_id)
            zip_file_name = ReleaseFileNames().get_chemical_shifts(accession=self.pdb_id, for_release=False)
            temp_file_path = self.get_remote_ftp_file(url=url, filename=zip_file_name)
        else:
            file_path = self.__local_ftp.get_chemical_shifts_fname(accession=self.pdb_id)
            logger.debug('checking local chemical shift filepath: {}'.format(file_path))
            return self.check_filename(file_path)
        logger.debug('final chemical shift filepath: {}'.format(temp_file_path))
        return temp_file_path

    def get_nmr_data(self):
        """
        Get the PDB combined NMR data file - from OneDep then local FTP and then the remote FTP
        :return: file name if present or None
        """
        if not self.__local_ftp.get_ftp_pdb():
            url = self.__remote_ftp.get_nmr_data_fname(self.pdb_id)
            zip_file_name = ReleaseFileNames().get_nmr_data(accession=self.pdb_id, for_release=False)
            temp_file_path = self.get_remote_ftp_file(url=url, filename=zip_file_name)
        else:
            file_path = self.__local_ftp.get_nmr_data_fname(accession=self.pdb_id)
            logger.debug('checking local NMR data filepath: {}'.format(file_path))
            return self.check_filename(file_path)
        logger.debug('final NMR data filepath: {}'.format(temp_file_path))
        return temp_file_path

    def get_remote_ftp_file(self, *, url, filename):
        """
        Get a file from the remote FTP
        :param url: path for download
        :param filename: filename without path
        :return: file path or None if no file
        """
        if self.get_file_from_remote_ftp(url=url, filename=filename):
            file_path = os.path.join(self.get_temp_local_ftp_path(), filename)
            if os.path.exists(file_path):
                return file_path
        remove_local_temp_ftp(self.setup_local_temp_ftp(), require_empty=True)
        return None

    def get_file_from_remote_ftp(self, *, url, filename):
        """
        gets file from FTP site
        :param url: path for download
        :param filename: filename without path
        :return: True if it exists, False if it fails
        """
        try:
            logger.debug("About to get %s %s to %s", url, filename, self.get_temp_local_ftp_path())
            if self.grf is None:
                self.grf = GetRemoteFiles(server=self.server, cache=self.__cache)
            ret = self.grf.get_url(url=url, output_path=self.get_temp_local_ftp_path())
            logger.debug("ret is %s", ret)
            if ret:
                return True
        except ValueError as e:
            logger.error(str(e))
        return False

    def get_temp_local_ftp_path(self):
        return os.path.join(self.setup_local_temp_ftp(), self.pdb_id)

    def setup_local_temp_ftp(self, session_path=None):
        if not self.__local_ftp_path:
            if not session_path:
                session_path = self.session_path
            self.__local_ftp_path = setup_local_temp_ftp(temp_dir=self.__temp_local_ftp,
                                                         session_path=session_path,
                                                         suffix=self.pdb_id)
        return self.__local_ftp_path

    @staticmethod
    def check_filename(file_name):
        """
        check that a file name actually exists
        :param file_name: file name
        :return: file name if present, None if not
        """
        if file_name:
            if os.path.exists(file_name):
                return file_name
        return None

    def remove_local_temp_files(self):
        """Cleanup of local ftp directory if present"""
        logger.debug("Cleaning up FTP local directory %s", self.__local_ftp_path)
        if self.__local_ftp_path and os.path.exists(self.__local_ftp_path):
            remove_local_temp_ftp(self.__local_ftp_path, require_empty=False)

    def close_connection(self):
        # maintained for backward compatibility with ftp version
        if self.grf is not None:
            self.grf.disconnect()
            self.grf = None

