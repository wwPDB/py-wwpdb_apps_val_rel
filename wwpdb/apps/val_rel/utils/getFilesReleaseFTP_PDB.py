import logging
import os

from wwpdb.utils.config.ConfigInfo import getSiteId

from wwpdb.apps.val_rel.config.ValConfig import ValConfig
from wwpdb.apps.val_rel.utils.getRemoteFilesFTP import GetRemoteFiles, setup_local_temp_ftp, remove_local_temp_ftp
from wwpdb.io.locator.ReleaseFileNames import ReleaseFileNames
from wwpdb.io.locator.localFTPPathInfo import LocalFTPPathInfo

logger = logging.getLogger(__name__)


class getFilesReleaseFtpPDB(object):
    def __init__(self, pdbid, site_id=getSiteId()):
        self.__site_id = site_id
        self.__rf = ReleaseFileNames()
        self.__local_ftp = LocalFTPPathInfo()
        self.__temp_local_ftp = None
        vc = ValConfig(self.__site_id)
        self.server = vc.ftp_server
        self.session_path = vc.session_path
        site_url_prefix = vc.ftp_prefix
        self.__remote_ftp = LocalFTPPathInfo()
        self.__remote_ftp.set_ftp_pdb_root(site_url_prefix)
        self.url_prefix = self.__remote_ftp.get_ftp_pdb()
        self.pdb_id = pdbid
        self.__local_ftp_path = None

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

    def setup_local_temp_ftp(self, session_path=None):
        if not self.__local_ftp_path:
            if not session_path:
                session_path = self.session_path
            self.__local_ftp_path = setup_local_temp_ftp(temp_dir=self.__temp_local_ftp,
                                                         session_path=session_path,
                                                         suffix=self.pdb_id)
        return self.__local_ftp_path

    def get_temp_local_ftp_path(self):
        return os.path.join(self.setup_local_temp_ftp(),
                            self.pdb_id)

    def remove_local_temp_files(self):
        """Cleanup of local ftp diretcory if present"""

        logger.debug("Cleaning up FTP local directory %s", self.__local_ftp_path)
        if self.__local_ftp_path and os.path.exists(self.__local_ftp_path):
            remove_local_temp_ftp(self.__local_ftp_path, require_empty=False)


    def get_remote_ftp_file(self, file_path, filename):
        """
        Get a file from the remote FTP
        :param file_path: sub path to get to the file
        :param filename: filename to be downloaded
        :return: file path or None if no file
        """
        ok = self.get_file_from_remote_ftp(file_path=file_path, filename=filename)
        if ok:
            file_path = os.path.join(self.get_temp_local_ftp_path(), filename)
            if os.path.exists(file_path):
                return file_path
        remove_local_temp_ftp(self.setup_local_temp_ftp(), require_empty=True)
        return None

    def get_file_from_remote_ftp(self, file_path, filename):
        """
        gets file from FTP site
        :return: True if it exists, False if it fails
        """
        logger.debug("About to get %s %s to %s", file_path, filename, self.get_temp_local_ftp_path())
        grf = GetRemoteFiles(server=self.server, output_path=self.get_temp_local_ftp_path())
        ret = grf.get_url(directory=file_path, filename=filename)
        # logger.debug("ret is %s", ret)
        if ret:
            return True
        return False

    def get_model(self):
        """
        get the PDB model file - from OneDep then local FTP and then the remote FTP
        :param pdbid: PDB ID
        :return: file name if present or None
        """
        fpart = ReleaseFileNames().get_model(accession=self.pdb_id, for_release=False)
        file_path = os.path.join(self.get_temp_local_ftp_path(), fpart)
        file_name = self.check_filename(file_path)
        if not file_name:
            file_name = self.get_remote_ftp_file(file_path=self.__remote_ftp.get_model_path(),
                                                 filename=fpart)
        return file_name

    def get_sf(self):
        """
        get the PDB structure factor file - from OneDep then local FTP and then the remote FTP
        :param pdbid: PDB ID
        :return: file name if present or None
        """
        fpart = ReleaseFileNames().get_structure_factor(accession=self.pdb_id, for_release=False)
        file_path = os.path.join(self.get_temp_local_ftp_path(), fpart)
        file_name = self.check_filename(file_path)
        if not file_name:
            file_name = self.get_remote_ftp_file(file_path=self.__remote_ftp.get_sf_path(),
                                                 filename=fpart)
        return file_name

    def get_cs(self):
        """
        get the PDB chemical shift file - from OneDep then local FTP and then the remote FTP
        :param pdbid: PDB ID
        :return: file name if present or None
        """
        fpart = ReleaseFileNames().get_chemical_shifts(accession=self.pdb_id, for_release=False)
        file_path = os.path.join(self.get_temp_local_ftp_path(), fpart)                                                                                           
        file_name = self.check_filename(file_path)
        if not file_name:
            file_name = self.get_remote_ftp_file(file_path=self.__remote_ftp.get_cs_path(),
                                                 filename=fpart)
        return file_name

    def get_nmr_data(self):
        """
        Get the PDB combined NMR data file - from OneDep then local FTP and then the remote FTP
        :param pdbid: PDB ID
        :return: file name if present or None
        """
        fpart = ReleaseFileNames().get_nmr_data(accession=self.pdb_id, for_release=False)
        file_path = os.path.join(self.get_temp_local_ftp_path(), fpart)
        file_name = self.check_filename(file_path)
        if not file_name:
            file_name = self.get_remote_ftp_file(file_path=self.__remote_ftp.get_nmr_data_path(),
                                                 filename=fpart)

        return file_name
