import logging
import os
from typing import Optional

from wwpdb.io.locator.localFTPPathInfo import LocalFTPPathInfo
from wwpdb.io.locator.ReleaseFileNames import ReleaseFileNames

from wwpdb.apps.val_rel.config.ValConfig import ValConfig
from wwpdb.apps.val_rel.utils.getFilesReleaseBase import GetFilesReleaseBasePDB, raise_no_pdb
from wwpdb.apps.val_rel.utils.http_protocol.getRemoteFilesHTTP import (
    GetRemoteFilesHttp,
    remove_local_temp_http,
    setup_local_temp_http,
)

logger = logging.getLogger(__name__)


class getFilesReleaseHttpPDB(GetFilesReleaseBasePDB):
    def __init__(self, pdbid: Optional[str], site_id: Optional[str] = None, cache: Optional[str] = None) -> None:
        super().__init__(pdbid=pdbid, site_id=site_id, cache=cache)
        self.__cache = cache

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
        self.__local_http_path: Optional[str] = None

        self.__grf: Optional[GetRemoteFilesHttp] = GetRemoteFilesHttp(
            server=self.__server, cache=self.__cache, site_id=self.__site_id
        )

    def get_model(self) -> Optional[str]:
        """
        get the PDB model file - from OneDep then local FTP and then the remote HTTP
        :return: file name if present or None
        """
        if self.__pdb_id is None:
            raise_no_pdb()

        url = self.__remote_http.get_model_fname(self.__pdb_id)
        zip_file_name = ReleaseFileNames().get_model(accession=self.__pdb_id, for_release=False)
        temp_file_path = self.__get_remote_http_file(url=url, filename=zip_file_name)

        logger.debug("final model filepath: %s", temp_file_path)
        return temp_file_path

    def get_sf(self) -> Optional[str]:
        """
        get the PDB structure factor file - from OneDep then local FTP and then the remote HTTP
        :return: file name if present or None
        """
        if self.__pdb_id is None:
            raise_no_pdb()

        url = self.__remote_http.get_structure_factors_fname(self.__pdb_id)
        zip_file_name = ReleaseFileNames().get_structure_factor(accession=self.__pdb_id, for_release=False)
        temp_file_path = self.__get_remote_http_file(url=url, filename=zip_file_name)

        logger.debug("final structure factor filepath: %s", temp_file_path)
        return temp_file_path

    def get_cs(self) -> Optional[str]:
        """
        get the PDB chemical shift file - from OneDep then local FTP and then the remote HTP
        :return: file name if present or None
        """
        if self.__pdb_id is None:
            raise_no_pdb()

        url = self.__remote_http.get_chemical_shifts_fname(self.__pdb_id)
        zip_file_name = ReleaseFileNames().get_chemical_shifts(accession=self.__pdb_id, for_release=False)
        temp_file_path = self.__get_remote_http_file(url=url, filename=zip_file_name)

        logger.debug("final chemical shift filepath: %s", temp_file_path)
        return temp_file_path

    def get_nmr_data(self) -> Optional[str]:
        """
        Get the PDB combined NMR data file - from OneDep then local FTP and then the remote HTTP
        :return: file name if present or None
        """
        if self.__pdb_id is None:
            raise_no_pdb()

        url = self.__remote_http.get_nmr_data_fname(self.__pdb_id)
        zip_file_name = ReleaseFileNames().get_nmr_data(accession=self.__pdb_id, for_release=False)
        temp_file_path = self.__get_remote_http_file(url=url, filename=zip_file_name)

        logger.debug("final NMR data filepath: %s", temp_file_path)
        return temp_file_path

    def __get_remote_http_file(self, url: str, filename: str) -> Optional[str]:
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

    def __get_file_from_remote_http(self, url: str, filename: str) -> bool:
        """
        gets file from HTTP site
        :param url: path for download
        :param filename: filename without path
        :return: True if it exists, False if it fails
        """
        try:
            logger.debug("About to get %s %s to %s", url, filename, self.__get_temp_local_http_path())
            if self.__grf is None:
                self.__grf = GetRemoteFilesHttp(server=self.__server, cache=self.__cache)
            ret = self.__grf.get_url(url=url, output_path=self.__get_temp_local_http_path())
            logger.debug("ret is %s", ret)
            if ret:
                return True
        except ValueError as e:
            logger.error(str(e))
        return False

    def __get_temp_local_http_path(self) -> str:
        if not self.__pdb_id:
            emsg = "PDB ID must be specified"
            raise ValueError(emsg)
        return os.path.join(self.__setup_local_temp_http(), self.__pdb_id)

    def __setup_local_temp_http(self, session_path: Optional[str] = None) -> str:
        """Creats a session directory local file name for download - unles using local ftp tree"""
        if not self.__local_http_path:
            if not session_path:
                session_path = self.__session_path
            if not self.__pdb_id:
                emsg = "PDB ID must be specified"
                raise ValueError(emsg)
            self.__local_http_path = setup_local_temp_http(
                temp_dir=self.__temp_local_ftp, session_path=session_path, suffix=self.__pdb_id
            )
        return self.__local_http_path

    def remove_local_temp_files(self) -> None:
        """Cleanup of local ftp directory if present"""
        logger.debug("Cleaning up HTTP local directory %s", self.__local_http_path)
        if self.__local_http_path and os.path.exists(self.__local_http_path):
            remove_local_temp_http(self.__local_http_path, require_empty=False)

    def close_connection(self) -> None:
        # maintained for backward compatibility with ftp version
        if self.__grf is not None:
            self.__grf.disconnect()
            self.__grf = None
