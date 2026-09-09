import logging
import os
from typing import Optional

from wwpdb.io.locator.localFTPPathInfo import LocalFTPPathInfo
from wwpdb.utils.config.ConfigInfo import getSiteId

from wwpdb.apps.val_rel.utils.getFilesReleaseBase import GetFilesReleaseBasePDB, raise_no_pdb

logger = logging.getLogger(__name__)


class getFilesReleaseLocal_PDB(GetFilesReleaseBasePDB):
    def __init__(self, pdbid: Optional[str], site_id: Optional[str] = None, cache: Optional[str] = None) -> None:
        if site_id is None:
            site_id = getSiteId()
        super().__init__(pdbid=pdbid, site_id=site_id, cache=cache)

        self.__local_ftp = LocalFTPPathInfo()
        self.__pdb_id = pdbid

    @staticmethod
    def __check_filename(file_name: str) -> Optional[str]:
        """
        check that a file name actually exists
        :param file_name: file name
        :return: file name if present, None if not
        """
        if file_name:
            if os.path.exists(file_name):
                return file_name
        return None

    def get_model(self) -> Optional[str]:
        """
        get the PDB model file - from OneDep then local FTP and then the remote FTP
        :param pdbid: PDB ID
        :return: file name if present or None
        """
        if self.__pdb_id is None:
            raise_no_pdb()

        file_path = self.__local_ftp.get_model_fname(accession=self.__pdb_id)
        logger.debug("checking local model filepath: %s", file_path)
        file_name = self.__check_filename(file_path)
        logger.debug("final model filepath: %s", file_name)
        return file_name

    def get_sf(self) -> Optional[str]:
        """
        get the PDB structure factor file - from OneDep then local FTP and then the remote FTP
        :param pdbid: PDB ID
        :return: file name if present or None
        """
        if self.__pdb_id is None:
            raise_no_pdb()

        file_path = self.__local_ftp.get_structure_factors_fname(accession=self.__pdb_id)
        logger.debug("checking local structure factor filepath: %s", file_path)
        file_name = self.__check_filename(file_path)

        logger.debug("final structure factor filepath: %s", file_name)
        return file_name

    def get_cs(self) -> Optional[str]:
        """
        get the PDB chemical shift file - from OneDep then local FTP and then the remote FTP
        :param pdbid: PDB ID
        :return: file name if present or None
        """
        if self.__pdb_id is None:
            raise_no_pdb()

        file_path = self.__local_ftp.get_chemical_shifts_fname(accession=self.__pdb_id)
        logger.debug("checking local chemical shift filepath: %s", file_path)
        file_name = self.__check_filename(file_path)
        logger.debug("final chemical shift filepath: %s", file_name)
        return file_name

    def get_nmr_data(self) -> Optional[str]:
        """
        Get the PDB combined NMR data file - from OneDep then local FTP and then the remote FTP
        :param pdbid: PDB ID
        :return: file name if present or None
        """
        file_path: Optional[str] = None

        if self.__pdb_id is None:
            raise_no_pdb()
        file_path = self.__local_ftp.get_nmr_data_fname(accession=self.__pdb_id)
        logger.debug("checking local NMR data filepath: %s", file_path)
        file_name = self.__check_filename(file_path)

        logger.debug("final NMR data filepath: %s", file_name)
        return file_name

    def close_connection(self) -> None:
        """Compatibility function to close the connection to the remote FTP server if it exists"""

    def remove_local_temp_files(self) -> None:
        """Removes any temporary directories directories."""
