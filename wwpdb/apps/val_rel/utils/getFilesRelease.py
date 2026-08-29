import logging
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, Type

from wwpdb.io.locator.localFTPPathInfo import LocalFTPPathInfo
from wwpdb.utils.config.ConfigInfo import getSiteId

from wwpdb.apps.val_rel.config.ValConfig import ValConfig
from wwpdb.apps.val_rel.utils.ftp_protocol.getFilesReleaseFTP_EMDB import getFilesReleaseFtpEMDB
from wwpdb.apps.val_rel.utils.ftp_protocol.getFilesReleaseFTP_PDB import getFilesReleaseFtpPDB
from wwpdb.apps.val_rel.utils.getFilesReleaseBase import GetFilesReleaseBaseEMDB, GetFilesReleaseBasePDB
from wwpdb.apps.val_rel.utils.getFilesReleaseOneDep import getFilesReleaseOneDep
from wwpdb.apps.val_rel.utils.http_protocol.getFilesReleaseHTTP_EMDB import getFilesReleaseHttpEMDB
from wwpdb.apps.val_rel.utils.http_protocol.getFilesReleaseHTTP_PDB import getFilesReleaseHttpPDB
from wwpdb.apps.val_rel.utils.local_archive_protocol.getFilesReleaseLocal_EMDB import getFilesReleaseLocal_EMDB
from wwpdb.apps.val_rel.utils.local_archive_protocol.getFilesReleaseLocal_PDB import getFilesReleaseLocal_PDB

logger = logging.getLogger(__name__)


class FileSource(Enum):
    NONE = auto()  # When none found
    ONEDEP_REL = auto()  # OneDep for_release/{added/modified/emd}
    ONEDEP_PREV = auto()  # Onedep for_release/previous/....
    REMOTE = auto()  # Public archive
    RUNDIR = auto()  # A local running directory

    @classmethod
    def get_default(cls) -> "FileSource":
        return cls.NONE


class FileContext(Enum):
    UNKNOWN = auto()
    MODEL = auto()
    SF = auto()
    CS = auto()
    NMR_DATA = auto()
    EMDB_XML = auto()
    EMDB_VOL = auto()
    EMDB_FSC = auto()
    EMDB_METADATA = auto()

    @classmethod
    def get_default(cls) -> "FileContext":
        return cls.UNKNOWN


@dataclass
class File:
    path: Optional[str] = None
    context: FileContext = FileContext.UNKNOWN
    loc: FileSource = FileSource.NONE


class getFilesRelease:
    """Class to access prior/public release files"""

    __files_pdb_func: Type[GetFilesReleaseBasePDB]
    __files_emdb_func: Type[GetFilesReleaseBaseEMDB]
    __release_file_from_remote_pdb: GetFilesReleaseBasePDB
    __release_file_from_remote_emdb: GetFilesReleaseBaseEMDB

    def __init__(
        self,
        pdb_id: Optional[str] = None,
        emdb_id: Optional[str] = None,
        siteID: Optional[str] = None,
        cache: Optional[str] = None,
    ) -> None:
        if siteID is None:
            siteID = getSiteId()
        self.__siteID = siteID
        self.__pdb_id = pdb_id
        self.__emdb_id = emdb_id
        self.__cache = cache
        self.__sf_current = False
        self.__cs_current = False
        self.__em_xml_current = False

        # Determine which routing
        config = ValConfig(site_id=siteID)

        local_ftp = LocalFTPPathInfo()

        # Handle PDB
        if local_ftp.get_ftp_pdb():
            self.__files_pdb_func = getFilesReleaseLocal_PDB
        elif config.val_rel_protocol in ["http", "https"]:
            self.__files_pdb_func = getFilesReleaseHttpPDB
        else:
            self.__files_pdb_func = getFilesReleaseFtpPDB

        # Handle EMDB
        if local_ftp.get_ftp_emdb():
            self.__files_emdb_func = getFilesReleaseLocal_EMDB
        elif config.val_rel_protocol in ["http", "https"]:
            self.__files_emdb_func = getFilesReleaseHttpEMDB
        else:
            self.__files_emdb_func = getFilesReleaseFtpEMDB

        self.__release_file_from_onedep = getFilesReleaseOneDep(siteID=self.__siteID, pdb_id=pdb_id, emdb_id=emdb_id)
        self.__release_file_from_remote_emdb = self.__files_emdb_func(
            site_id=self.__siteID, emdbid=emdb_id, cache=self.__cache
        )
        self.__release_file_from_remote_pdb = self.__files_pdb_func(
            site_id=self.__siteID, pdbid=pdb_id, cache=self.__cache
        )

    def close_connections(self) -> None:
        """This method should be used to close all open
        connections in subclasses.
        """
        self.__release_file_from_remote_pdb.close_connection()
        self.__release_file_from_remote_emdb.close_connection()

    def set_pdb_id(self, pdb_id: str) -> None:
        """Sets up pdb_id for processing release files"""

        # Do not create a new path if same pdb_id. Prevents excessive downloads
        if self.__pdb_id != pdb_id:
            self.__pdb_id = pdb_id
            self.__release_file_from_onedep = getFilesReleaseOneDep(
                siteID=self.__siteID, pdb_id=self.__pdb_id, emdb_id=self.__emdb_id
            )
            if self.__release_file_from_remote_pdb is not None:
                self.__release_file_from_remote_pdb.close_connection()

            self.__release_file_from_remote_pdb = self.__files_pdb_func(
                site_id=self.__siteID, pdbid=pdb_id, cache=self.__cache
            )

    def set_emdb_id(self, emdb_id: str) -> None:
        """Sets up emdb_id for processing release files"""

        # Do not create a new path if same emdb_id
        if self.__emdb_id != emdb_id:
            self.__emdb_id = emdb_id
            self.__release_file_from_onedep = getFilesReleaseOneDep(
                siteID=self.__siteID, pdb_id=self.__pdb_id, emdb_id=emdb_id
            )

            if self.__release_file_from_remote_emdb is not None:
                self.__release_file_from_remote_emdb.close_connection()

            self.__release_file_from_remote_emdb = self.__files_emdb_func(
                site_id=self.__siteID, emdbid=emdb_id, cache=self.__cache
            )

    def remove_local_temp_files(self) -> None:
        """Removes any temporary FTP directories"""
        self.__release_file_from_remote_pdb.remove_local_temp_files()
        self.__release_file_from_remote_emdb.remove_local_temp_files()

    def get_model(self) -> File:
        """
        get the PDB model file - from OneDep then local/remote FTP
        :param pdbid: PDB ID
        :return: file name if present or None
        """
        loc = FileSource.NONE
        file_name, cur = self.__release_file_from_onedep.get_model()
        if not file_name:
            file_name = self.__release_file_from_remote_pdb.get_model()
            if file_name:
                loc = FileSource.REMOTE
        else:
            loc = FileSource.ONEDEP_REL if cur else FileSource.ONEDEP_PREV
        return File(file_name, FileContext.MODEL, loc)

    def get_sf(self) -> File:
        """
        get the PDB structure factor file - from OneDep then local FTP
        :param pdbid: PDB ID
        :return: file name if present or None
        """
        loc = FileSource.NONE
        file_name, self.__sf_current = self.__release_file_from_onedep.get_sf()
        if not file_name:
            file_name = self.__release_file_from_remote_pdb.get_sf()
            if file_name:
                loc = FileSource.REMOTE
        else:
            loc = FileSource.ONEDEP_REL if self.__sf_current else FileSource.ONEDEP_PREV
        return File(file_name, FileContext.SF, loc)

    def get_cs(self) -> File:
        """
        get the PDB chemical shift file - from OneDep then local FTP
        :param pdbid: PDB ID
        :return: file name if present or None
        """
        loc = FileSource.NONE
        file_name, self.__cs_current = self.__release_file_from_onedep.get_cs()
        if not file_name:
            file_name = self.__release_file_from_remote_pdb.get_cs()
            if file_name:
                loc = FileSource.REMOTE
        else:
            loc = FileSource.ONEDEP_REL if self.__cs_current else FileSource.ONEDEP_PREV
        return File(file_name, FileContext.CS, loc)

    def get_nmr_data(self) -> File:
        """
        Get the PDB combined NMR data file - from OneDep then local FTP
        :param pdbid: PDB ID
        :return: file name if present or None
        """
        loc = FileSource.NONE
        file_name, self.__cs_current = self.__release_file_from_onedep.get_nmr_data()
        if not file_name:
            file_name = self.__release_file_from_remote_pdb.get_nmr_data()
            if file_name:
                loc = FileSource.REMOTE
        else:
            loc = FileSource.ONEDEP_REL if self.__cs_current else FileSource.ONEDEP_PREV
        return File(file_name, FileContext.NMR_DATA, loc)

    def get_emdb_xml(self) -> File:
        loc = FileSource.NONE
        file_name, self.__em_xml_current = self.__release_file_from_onedep.get_emdb_xml()
        if not file_name:
            file_name = self.__release_file_from_remote_emdb.get_emdb_xml()
            if file_name:
                loc = FileSource.REMOTE
        else:
            loc = FileSource.ONEDEP_REL if self.__em_xml_current else FileSource.ONEDEP_PREV

        return File(file_name, FileContext.EMDB_XML, loc)

    def get_emdb_volume(self) -> File:
        loc = FileSource.NONE
        file_name, cur = self.__release_file_from_onedep.get_emdb_volume()
        if not file_name:
            file_name = self.__release_file_from_remote_emdb.get_emdb_volume()
            if file_name:
                loc = FileSource.REMOTE
        else:
            loc = FileSource.ONEDEP_REL if cur else FileSource.ONEDEP_PREV

        return File(file_name, FileContext.EMDB_VOL, loc)

    def get_emdb_metadata(self) -> File:
        loc = FileSource.NONE
        file_name, cur = self.__release_file_from_onedep.get_emdb_metadata()
        if not file_name:
            file_name = self.__release_file_from_remote_emdb.get_emdb_metadata()
            if file_name:
                loc = FileSource.REMOTE
        else:
            loc = FileSource.ONEDEP_REL if cur else FileSource.ONEDEP_PREV
        return File(file_name, FileContext.EMDB_METADATA, loc)

    def get_emdb_fsc(self) -> File:
        loc = FileSource.NONE
        file_name, cur = self.__release_file_from_onedep.get_emdb_fsc()
        if not file_name:
            file_name = self.__release_file_from_remote_emdb.get_emdb_fsc()
            if file_name:
                loc = FileSource.REMOTE
        else:
            loc = FileSource.ONEDEP_REL if cur else FileSource.ONEDEP_PREV

        return File(file_name, FileContext.EMDB_FSC, loc)

    def is_sf_current(self) -> bool:
        return self.__sf_current

    def is_cs_current(self) -> bool:
        return self.__cs_current

    def is_em_xml_current(self) -> bool:
        return self.__em_xml_current

    def set_cache(self, fpath: Optional[str]) -> None:
        self.__cache = fpath
