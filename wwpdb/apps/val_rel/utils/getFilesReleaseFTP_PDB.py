import logging
import os
import tempfile

from wwpdb.io.locator.ReleaseFileNames import ReleaseFileNames
from wwpdb.io.locator.localFTPPathInfo import LocalFTPPathInfo
from wwpdb.utils.config.ConfigInfo import ConfigInfo, getSiteId

from wwpdb.apps.val_rel.utils.getRemoteFilesFTP import GetRemoteFiles

logger = logging.getLogger(__name__)


class getFilesReleaseFtpPDB:
    def __init__(self, pdbid, site_id=getSiteId(), local_ftp_pdb_path=None):
        self.__site_id = site_id
        self.__cI = ConfigInfo(self.__site_id)
        self.__rf = ReleaseFileNames()
        self.__local_ftp = LocalFTPPathInfo()
        self.__temp_local_ftp = None
        self.server = 'ftp.ebi.ac.uk'
        self.url_prefix = 'pub/databases/emdb/structures'
        self.pdb_id = pdbid

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

    def get_model(self):
        """
        get the PDB model file - from OneDep then local FTP
        :param pdbid: PDB ID
        :return: file name if present or None
        """
        file_name = self.check_filename(self.__local_ftp.get_model_fname(accession=self.pdb_id))
        return file_name

    def get_sf(self):
        """
        get the PDB structure factor file - from OneDep then local FTP
        :param pdbid: PDB ID
        :return: file name if present or None
        """
        file_name = self.check_filename(self.__local_ftp.get_structure_factors_fname(accession=self.pdb_id))
        return file_name

    def get_cs(self):
        """
        get the PDB chemical shift file - from OneDep then local FTP
        :param pdbid: PDB ID
        :return: file name if present or None
        """
        file_name = self.check_filename(self.__local_ftp.get_chemical_shifts_fname(accession=self.pdb_id))
        return file_name

    def get_nmr_data(self):
        """
        Get the PDB combined NMR data file - from OneDep then local FTP
        :param pdbid: PDB ID
        :return: file name if present or None
        """
        file_name = self.check_filename(self.__local_ftp.get_nmr_data_fname(accession=self.pdb_id))
        return file_name

