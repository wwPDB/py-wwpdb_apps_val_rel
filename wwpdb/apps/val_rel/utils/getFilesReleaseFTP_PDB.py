import logging
import os
from typing import Optional, cast

from wwpdb.io.locator.localFTPPathInfo import LocalFTPPathInfo
from wwpdb.io.locator.ReleaseFileNames import ReleaseFileNames
from wwpdb.utils.config.ConfigInfo import getSiteId

from wwpdb.apps.val_rel.config.ValConfig import ValConfig
from wwpdb.apps.val_rel.utils.getFilesReleaseBase import GetFilesReleaseBasePDB
from wwpdb.apps.val_rel.utils.getRemoteFilesFTP import GetRemoteFiles, remove_local_temp_ftp, setup_local_temp_ftp

logger = logging.getLogger(__name__)


class getFilesReleaseFtpPDB(GetFilesReleaseBasePDB):
    def __init__(self, pdbid: Optional[str], site_id: Optional[str] = None, cache: Optional[str] = None) -> None:
        if site_id is None:
            site_id = getSiteId()
        self.__site_id = site_id
        self.__cache = cache
        super().__init__(pdbid=pdbid, site_id=site_id, cache=cache)

        self.__rf = ReleaseFileNames()
        self.__local_ftp = LocalFTPPathInfo()
        self.__temp_local_ftp = None  # Used once as a constant!!!
        vc = ValConfig(self.__site_id)
        self.server = vc.ftp_server
        self.session_path = vc.session_path
        site_url_prefix = vc.ftp_prefix
        self.__remote_ftp = LocalFTPPathInfo()
        self.__remote_ftp.set_ftp_pdb_root(site_url_prefix)
        self.url_prefix = self.__remote_ftp.get_ftp_pdb()
        self.pdb_id = pdbid
        self.__local_ftp_path: Optional[str] = None
        self.grf = None

        if not self.__local_ftp.get_ftp_pdb():
            self.grf = GetRemoteFiles(server=self.server, cache=self.__cache)

    @staticmethod
    def check_filename(file_name: str) -> Optional[str]:
        """
        check that a file name actually exists
        :param file_name: file name
        :return: file name if present, None if not
        """
        if file_name:
            if os.path.exists(file_name):
                return file_name
        return None

    def setup_local_temp_ftp(self, session_path: Optional[str] = None) -> str:
        if not self.__local_ftp_path:
            if not session_path:
                session_path = self.session_path
            if not self.pdb_id:
                emsg = "PDB ID is not set. Cannot setup local temp FTP path."
                raise ValueError(emsg)
            self.__local_ftp_path = setup_local_temp_ftp(
                temp_dir=self.__temp_local_ftp, session_path=session_path, suffix=self.pdb_id
            )  # self.__local_ftp_path will be set here - so have a string
        return self.__local_ftp_path

    def get_temp_local_ftp_path(self) -> str:
        if not self.pdb_id:
            emsg = "PDB ID is not set. Cannot get local temp FTP path."
            raise ValueError(emsg)
        return os.path.join(self.setup_local_temp_ftp(), self.pdb_id)

    def remove_local_temp_files(self) -> None:
        """Cleanup of local ftp directory if present"""

        logger.debug("Cleaning up FTP local directory %s", self.__local_ftp_path)
        if self.__local_ftp_path and os.path.exists(self.__local_ftp_path):
            remove_local_temp_ftp(self.__local_ftp_path, require_empty=False)

    def get_remote_ftp_file(self, file_path: str, filename: str) -> Optional[str]:
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

    def get_file_from_remote_ftp(self, file_path: str, filename: str) -> bool:
        """
        gets file from FTP site
        :return: True if it exists, False if it fails
        """
        logger.debug("About to get %s %s to %s", file_path, filename, self.get_temp_local_ftp_path())

        if self.grf is None:
            logger.warning("There was no existing ftp connection. Opening new connection now...")
            self.grf = GetRemoteFiles(server=self.server, cache=self.__cache)

        ret = self.grf.get_url(output_path=self.get_temp_local_ftp_path(), directory=file_path, filename=filename)
        # logger.debug("ret is %s", ret)
        if ret:
            return True
        return False

    def get_model(self) -> Optional[str]:
        """
        get the PDB model file - from OneDep then local FTP and then the remote FTP
        :param pdbid: PDB ID
        :return: file name if present or None
        """
        if self.__local_ftp.get_ftp_pdb():
            file_path = self.__local_ftp.get_model_fname(accession=self.pdb_id)
            logger.debug("checking local model filepath: %s", file_path)
            file_name = self.check_filename(file_path)
        else:
            fpart = self.__rf.get_model(accession=self.pdb_id, for_release=False)
            file_name = self.get_remote_ftp_file(file_path=self.__remote_ftp.get_model_path(), filename=fpart)
        logger.debug("final model filepath: %s", file_name)
        return file_name

    def get_sf(self) -> Optional[str]:
        """
        get the PDB structure factor file - from OneDep then local FTP and then the remote FTP
        :param pdbid: PDB ID
        :return: file name if present or None
        """
        if self.__local_ftp.get_ftp_pdb():
            file_path = self.__local_ftp.get_structure_factors_fname(accession=self.pdb_id)
            # file_path = os.path.join(self.get_temp_local_ftp_path(), fpart)
            logger.debug("checking local structure factor filepath: %s", file_path)
            file_name = self.check_filename(file_path)
        else:
            fpart = self.__rf.get_structure_factor(accession=self.pdb_id, for_release=False)
            file_name = self.get_remote_ftp_file(file_path=self.__remote_ftp.get_sf_path(), filename=fpart)
        logger.debug("final structure factor filepath: %s", file_name)
        return file_name

    def get_cs(self) -> Optional[str]:
        """
        get the PDB chemical shift file - from OneDep then local FTP and then the remote FTP
        :param pdbid: PDB ID
        :return: file name if present or None
        """
        # file_path = os.path.join(self.get_temp_local_ftp_path(), fpart)
        if self.__local_ftp.get_ftp_pdb():
            file_path = self.__local_ftp.get_chemical_shifts_fname(accession=self.pdb_id)
            logger.debug("checking local chemical shift filepath: %s", file_path)
            file_name = self.check_filename(file_path)
        else:
            fpart = self.__rf.get_chemical_shifts(accession=self.pdb_id, for_release=False)
            file_name = self.get_remote_ftp_file(file_path=self.__remote_ftp.get_cs_path(), filename=fpart)
        logger.debug("final chemical shift filepath: %s", file_name)
        return file_name

    def get_nmr_data(self) -> Optional[str]:
        """
        Get the PDB combined NMR data file - from OneDep then local FTP and then the remote FTP
        :param pdbid: PDB ID
        :return: file name if present or None
        """
        file_path: Optional[str] = None
        if self.__local_ftp.get_ftp_pdb():
            file_path = cast("str", self.__local_ftp.get_nmr_data_fname(accession=self.pdb_id))
            # file_path = os.path.join(self.get_temp_local_ftp_path(), fpart)
            logger.debug("checking local NMR data filepath: %s", file_path)
            file_name = self.check_filename(file_path)
        else:
            fpart = self.__rf.get_nmr_data(accession=self.pdb_id, for_release=False)
            file_name = self.get_remote_ftp_file(file_path=self.__remote_ftp.get_nmr_data_path(), filename=fpart)

        logger.debug("final NMR data filepath: %s", file_name)
        return file_name

    def close_connection(self) -> None:
        if self.grf is not None:
            self.grf.disconnect()
            self.grf = None
