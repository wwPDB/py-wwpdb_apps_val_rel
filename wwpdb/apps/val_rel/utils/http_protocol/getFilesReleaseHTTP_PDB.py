import os
import logging
from wwpdb.io.locator.ReleaseFileNames import ReleaseFileNames
from wwpdb.io.locator.localFTPPathInfo import LocalFTPPathInfo
from wwpdb.apps.val_rel.config.ValConfig import ValConfig
from wwpdb.apps.val_rel.utils.http_protocol.getRemoteFilesHTTP import GetRemoteFilesHttp, setup_local_temp_http, remove_local_temp_http

logger = logging.getLogger(__name__)


class getFilesReleaseHttpPDB(object):
    def __init__(self, pdbid, site_id=None, cache=None):
        self.__cache = cache

        # This provides access to local ftp tree.  If SITE_PDB_FTP_ROOT_DIR site-config variable not set
        # get_ftp_pdb() will return ""
        self.__local_ftp = LocalFTPPathInfo()

        self.__temp_local_ftp = None
        self.__site_id = site_id

        vc = ValConfig(site_id)
        self.__server = vc.http_server
        self.__session_path = vc.session_path

        http_prefix = vc.http_prefix
        protocol = vc.val_rel_protocol
        url_prefix = "%s://%s%s" % (protocol, self.__server, http_prefix)


        # This is refencing public archive path 
        self.__remote_http = LocalFTPPathInfo()
        self.__remote_http.set_ftp_pdb_root(url_prefix)

        self.__pdb_id = pdbid

        # The local sessiondir download path
        self.__local_http_path = None

        self.grf = None

        if not self.__local_ftp.get_ftp_pdb():
            self.grf = GetRemoteFilesHttp(server=self.__server, cache=self.__cache, site_id=self.__site_id)

    def get_model(self):
        """
        get the PDB model file - from OneDep then local FTP and then the remote HTTP
        :return: file name if present or None
        """
        if not self.__local_ftp.get_ftp_pdb():
            url = self.__remote_http.get_model_fname(self.__pdb_id)
            zip_file_name = ReleaseFileNames().get_model(accession=self.__pdb_id, for_release=False)
            temp_file_path = self.__get_remote_http_file(url=url, filename=zip_file_name)
        else:
            file_path = self.__local_ftp.get_model_fname(accession=self.__pdb_id)
            logger.debug('checking local model filepath: {}'.format(file_path))
            return self.__check_filename(file_path)
        logger.debug('final model filepath: {}'.format(temp_file_path))
        return temp_file_path

    def get_sf(self):
        """
        get the PDB structure factor file - from OneDep then local FTP and then the remote HTTP
        :return: file name if present or None
        """
        if not self.__local_ftp.get_ftp_pdb():
            url = self.__remote_http.get_structure_factors_fname(self.__pdb_id)
            zip_file_name = ReleaseFileNames().get_structure_factor(accession=self.__pdb_id, for_release=False)
            temp_file_path = self.__get_remote_http_file(url=url, filename=zip_file_name)
        else:
            file_path = self.__local_ftp.get_structure_factors_fname(accession=self.__pdb_id)
            logger.debug('checking local structure factor filepath: {}'.format(file_path))
            return self.__check_filename(file_path)
        logger.debug('final structure factor filepath: {}'.format(temp_file_path))
        return temp_file_path

    def get_cs(self):
        """
        get the PDB chemical shift file - from OneDep then local FTP and then the remote HTP
        :return: file name if present or None
        """
        if not self.__local_ftp.get_ftp_pdb():
            url = self.__remote_http.get_chemical_shifts_fname(self.__pdb_id)
            zip_file_name = ReleaseFileNames().get_chemical_shifts(accession=self.__pdb_id, for_release=False)
            temp_file_path = self.__get_remote_http_file(url=url, filename=zip_file_name)
        else:
            file_path = self.__local_ftp.get_chemical_shifts_fname(accession=self.__pdb_id)
            logger.debug('checking local chemical shift filepath: {}'.format(file_path))
            return self.__check_filename(file_path)
        logger.debug('final chemical shift filepath: {}'.format(temp_file_path))
        return temp_file_path

    def get_nmr_data(self):
        """
        Get the PDB combined NMR data file - from OneDep then local FTP and then the remote HTTP
        :return: file name if present or None
        """
        if not self.__local_ftp.get_ftp_pdb():
            url = self.__remote_http.get_nmr_data_fname(self.__pdb_id)
            zip_file_name = ReleaseFileNames().get_nmr_data(accession=self.__pdb_id, for_release=False)
            temp_file_path = self.__get_remote_http_file(url=url, filename=zip_file_name)
        else:
            file_path = self.__local_ftp.get_nmr_data_fname(accession=self.__pdb_id)
            logger.debug('checking local NMR data filepath: {}'.format(file_path))
            return self.__check_filename(file_path)
        logger.debug('final NMR data filepath: {}'.format(temp_file_path))
        return temp_file_path

    def __get_remote_http_file(self, *, url, filename):
        """
        Get a file from the remote HTTP service - or cached
        :param url: path for download
        :param filename: filename without path
        :return: file path or None if no file
        """
        if self.__get_file_from_remote_http(url=url, filename=filename):
            file_path = os.path.join(self.__get_temp_local_http_path(), filename)
            if os.path.exists(file_path):
                return file_path
        # Failure - cleanup local directory if empty
        remove_local_temp_http(self.__setup_local_temp_http(), require_empty=True)
        return None

    def __get_file_from_remote_http(self, *, url, filename):
        """
        gets file from HTTP site
        :param url: path for download
        :param filename: filename without path
        :return: True if it exists, False if it fails
        """
        try:
            logger.debug("About to get %s %s to %s", url, filename, self.__get_temp_local_http_path())
            if self.grf is None:
                self.grf = GetRemoteFilesHttp(server=self.__server, cache=self.__cache)
            ret = self.grf.get_url(url=url, output_path=self.__get_temp_local_http_path())
            logger.debug("ret is %s", ret)
            if ret:
                return True
        except ValueError as e:
            logger.error(str(e))
        return False

    def __get_temp_local_http_path(self):
        return os.path.join(self.__setup_local_temp_http(), self.__pdb_id)

    def __setup_local_temp_http(self, session_path=None):
        """Creats a session directory local file name for download - unles using local ftp tree"""
        if not self.__local_http_path:
            if not session_path:
                session_path = self.__session_path
            self.__local_http_path = setup_local_temp_http(temp_dir=self.__temp_local_ftp,
                                                          session_path=session_path,
                                                          suffix=self.__pdb_id)
        return self.__local_http_path

    @staticmethod
    def __check_filename(file_name):
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
        logger.debug("Cleaning up HTTP local directory %s", self.__local_http_path)
        if self.__local_http_path and os.path.exists(self.__local_http_path):
            remove_local_temp_http(self.__local_http_path, require_empty=False)

    def close_connection(self):
        # maintained for backward compatibility with ftp version
        if self.grf is not None:
            self.grf.disconnect()
            self.grf = None
