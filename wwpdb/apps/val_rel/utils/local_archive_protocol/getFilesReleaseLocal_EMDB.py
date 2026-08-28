import logging
import os
from typing import Literal, Optional, cast

from wwpdb.io.locator.localFTPPathInfo import LocalFTPPathInfo
from wwpdb.io.locator.ReleaseFileNames import ReleaseFileNames
from wwpdb.utils.config.ConfigInfo import getSiteId

from wwpdb.apps.val_rel.config.ValConfig import ValConfig
from wwpdb.apps.val_rel.utils.ftp_protocol.getRemoteFilesFTP import (
    remove_local_temp_ftp,
    setup_local_temp_ftp,
)
from wwpdb.apps.val_rel.utils.getFilesReleaseBase import GetFilesReleaseBaseEMDB

logger = logging.getLogger(__name__)


class getFilesReleaseLocal_EMDB(GetFilesReleaseBaseEMDB):
    def __init__(
        self,
        emdbid: Optional[str],
        site_id: Optional[str] = None,
        local_ftp_emdb_path: Optional[str] = None,
        cache: Optional[str] = None,
    ) -> None:
        if site_id is None:
            site_id = getSiteId()

        super().__init__(emdbid=emdbid, site_id=site_id, local_ftp_emdb_path=local_ftp_emdb_path, cache=cache)
        self.__site_id = site_id
        self.__rf = ReleaseFileNames()
        self.__local_ftp = LocalFTPPathInfo()
        self.__local_ftp_emdb_path = local_ftp_emdb_path if local_ftp_emdb_path else self.__local_ftp.get_ftp_emdb()
        self.__temp_local_ftp: Optional[str] = None
        vc = ValConfig(self.__site_id)
        self.__session_path = vc.session_path
        site_url_prefix = vc.ftp_prefix
        l_ftp = LocalFTPPathInfo()
        l_ftp.set_ftp_emdb_root(site_url_prefix)
        self.__emdb_id = emdbid

    def get_local_ftp_path(self) -> str:
        return cast("str", self.__local_ftp.get_ftp_emdb())

    def set_local_ftp_path(self, ftp_path: str) -> None:
        self.__local_ftp.set_ftp_emdb_root(ftp_path)
        self.__local_ftp_emdb_path = ftp_path

    def get_emdb_subfolder(self, sub_folder: Literal["header", "map", "fsc", "metadata"]) -> str:
        if not self.__emdb_id:
            emsg = "EMDB ID is not set. Cannot get EMDB subfolder."
            raise ValueError(emsg)
        return os.path.join(self.__emdb_id, sub_folder)

    def emdb_xml_folder(self) -> str:
        return self.get_emdb_subfolder(sub_folder="header")

    def emdb_map_folder(self) -> str:
        return self.get_emdb_subfolder(sub_folder="map")

    def emdb_fsc_folder(self) -> str:
        return self.get_emdb_subfolder(sub_folder="fsc")

    def emdb_metadata_folder(self) -> str:
        return self.get_emdb_subfolder(sub_folder="metadata")

    def setup_local_temp_ftp(self, session_path: Optional[str] = None) -> str:
        if not self.__temp_local_ftp:
            if not session_path:
                session_path = self.__session_path
            if not self.__emdb_id:
                emsg = "EMDB ID is not set. Cannot setup local temp FTP."
                raise ValueError(emsg)
            self.__temp_local_ftp = setup_local_temp_ftp(
                temp_dir=self.__temp_local_ftp, suffix=self.__emdb_id, session_path=session_path
            )
        return self.__temp_local_ftp

    def remove_local_temp_files(self) -> None:
        """Cleanup of local ftp diretcory if present"""

        logger.debug("Cleaning up FTP EMDB local directory %s", self.__temp_local_ftp)
        if self.__temp_local_ftp and os.path.exists(self.__temp_local_ftp):
            remove_local_temp_ftp(self.__temp_local_ftp, require_empty=False)

    def set_temp_local_ftp_as_local_ftp_path(self) -> None:
        self.setup_local_temp_ftp()
        self.__local_ftp_emdb_path = self.__temp_local_ftp

    def get_temp_local_ftp_emdb_path(self) -> str:
        if not self.__emdb_id:
            emsg = "EMDB ID is not set. Cannot get EMDB temp local FTP path."
            raise ValueError(emsg)
        return os.path.join(self.setup_local_temp_ftp(), self.__emdb_id)

    def get_local_emdb_subfolder(self, emdb_path: str) -> Optional[str]:
        if self.__local_ftp_emdb_path:
            return os.path.join(self.__local_ftp_emdb_path, emdb_path)
        return None

    def get_emdb_local_ftp_file(self, emdb_path: str, filename: str) -> Optional[str]:
        local_ftp = self.get_local_emdb_subfolder(emdb_path=emdb_path)
        if local_ftp:
            file_path = os.path.join(local_ftp, filename)
            if os.path.exists(file_path):
                return file_path
        return None

    def get_emdb_local_ftp_single_file(self, filename: str) -> Optional[str]:
        if os.path.exists(self.get_temp_local_ftp_emdb_path()):
            file_path = os.path.join(self.get_temp_local_ftp_emdb_path(), filename)
            if os.path.exists(file_path):
                return file_path
        return None

    def get_emdb_xml(self) -> Optional[str]:
        logger.debug("EM XML")
        local_ftp = self.__local_ftp.get_ftp_emdb()
        logger.debug('local FTP path: "%s"', local_ftp)

        logger.debug("trying local FTP")
        file_name = self.get_emdb_local_ftp_file(
            filename=self.__rf.get_emdb_xml(self.__emdb_id), emdb_path=self.emdb_xml_folder()
        )

        logger.debug("returning: %s", file_name)
        return file_name

    def get_emdb_volume(self) -> Optional[str]:
        logger.debug("em volume")
        file_name: Optional[str] = None
        local_ftp = self.__local_ftp.get_ftp_emdb()
        logger.debug('local FTP path: "%s"', local_ftp)
        logger.debug("trying local FTP")
        file_name = self.get_emdb_local_ftp_file(
            filename=self.__rf.get_emdb_map(self.__emdb_id), emdb_path=self.emdb_map_folder()
        )

        logger.debug("returning: %s", file_name)
        return file_name

    def get_emdb_fsc(self) -> Optional[str]:
        logger.debug("FSC")
        local_ftp = self.__local_ftp.get_ftp_emdb()
        logger.debug('local FTP path: "%s"', local_ftp)
        logger.debug("trying local FTP")
        file_name = self.get_emdb_local_ftp_file(
            filename=self.__rf.get_emdb_fsc(self.__emdb_id), emdb_path=self.emdb_fsc_folder()
        )
        logger.debug("returning: %s", file_name)
        return file_name

    def get_emdb_metadata(self) -> Optional[str]:
        logger.debug("metadata")
        local_ftp = self.__local_ftp.get_ftp_emdb()
        logger.debug('local FTP path: "%s"', local_ftp)
        logger.debug("trying local FTP")
        file_name = self.get_emdb_local_ftp_file(
            filename=self.__rf.get_emdb_metadata(self.__emdb_id), emdb_path=self.emdb_metadata_folder()
        )
        logger.debug("returning: %s", file_name)
        return file_name

    def close_connection(self) -> None:
        """Compatibility function to close the connection to the remote FTP server if it exists"""
