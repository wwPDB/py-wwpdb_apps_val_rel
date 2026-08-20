import os
import platform
import sys
from typing import Any, Optional, TextIO

from wwpdb.utils.config.ConfigInfo import ConfigInfo  # noqa: E402

HERE = os.path.abspath(os.path.dirname(__file__))
TOPDIR = os.path.dirname(HERE)
TESTOUTPUT = os.path.join(HERE, "test-output", platform.python_version())
if not os.path.exists(TESTOUTPUT):
    os.makedirs(TESTOUTPUT)  # pragma: no cover


class MyConfigInfo(ConfigInfo):
    """A class to bypass setting of refdata"""

    def __init__(self, siteId: Optional[str] = None, verbose: bool = True, log: TextIO = sys.stderr) -> None:
        self._archive_path: Optional[str] = None
        self._session_path: Optional[str] = None
        self._protocol: Optional[str] = None
        self._ftp_server: Optional[str] = None
        self._ftp_prefix: Optional[str] = None
        self._local_pdb_archive_path: Optional[str] = None
        self._local_emdb_archive_path: Optional[str] = None
        self._http_server: Optional[str] = None
        self._http_server_prefix: Optional[str] = None
        super(MyConfigInfo, self).__init__(siteId=siteId, verbose=verbose, log=log)

    def get(self, keyWord: str, default: Any = None) -> Any:
        if keyWord == "SITE_ARCHIVE_STORAGE_PATH":
            val = self._archive_path
        elif keyWord == "FOR_RELEASE_DATA_PATH":
            val = default
        elif keyWord == "VAL_REL_PROTOCOL":
            val = self._protocol
        elif keyWord == "SITE_FTP_SERVER":
            val = self._ftp_server
        elif keyWord == "SITE_FTP_SERVER_PREFIX":
            val = self._ftp_prefix
        elif keyWord == "SITE_WEB_APPS_TOP_SESSIONS_PATH":
            val = self._session_path
        elif keyWord == "SITE_PDB_FTP_ROOT_DIR":
            val = self._local_pdb_archive_path
        elif keyWord == "SITE_EMDB_FTP_ROOT_DIR":
            val = self._local_emdb_archive_path
        elif keyWord == "SITE_HTTP_SERVER":
            val = self._http_server
        elif keyWord == "SITE_HTTP_SERVER_PREFIX":
            val = self._http_server_prefix
        elif keyWord in ("FOR_RELEASE_DATA_PATH", "SITE_WEB_APPS_SESSIONS_PATH"):
            # Legacy variables
            val = None

        else:  # pragma: no cover
            sys.stderr.write("XXXXX Unknown site config fetching %s\n" % keyWord)
            val = super(MyConfigInfo, self).get(keyWord=keyWord, default=default)
        # sys.stderr.write("XXXXX fetching %s %s\n" % (keyWord, val))
        return val


class StandardConfig(MyConfigInfo):
    def __init__(self, siteId: Optional[str] = None, verbose: bool = True, log: TextIO = sys.stderr) -> None:
        super(StandardConfig, self).__init__(siteId=siteId, verbose=verbose, log=log)
        self._archive_path = os.path.join(TESTOUTPUT, "data")
        self._session_path = os.path.join(TESTOUTPUT, "sessions")


class FtpStandardConfig(StandardConfig):
    def __init__(self, siteId: Optional[str] = None, verbose: bool = True, log: TextIO = sys.stderr) -> None:
        super(FtpStandardConfig, self).__init__(siteId=siteId, verbose=verbose, log=log)
        self._protocol = "ftp"
        self._ftp_server = "ftp.ebi.ac.uk"
        self._ftp_prefix = "/pub/databases"


class LocalPublicArchiveFtpConfig(FtpStandardConfig):
    """Class that enables the local data archive"""

    def __init__(self, siteId: Optional[str] = None, verbose: bool = True, log: TextIO = sys.stderr) -> None:
        super(LocalPublicArchiveFtpConfig, self).__init__(siteId=siteId, verbose=verbose, log=log)
        self._local_pdb_archive_path = os.path.join(HERE, "data")
        self._local_emdb_archive_path = os.path.join(HERE, "data")


class LocalPublicArchiveHttpConfig(LocalPublicArchiveFtpConfig):
    """Class that enables the local data archive with http protocol if not set"""

    def __init__(self, siteId: Optional[str] = None, verbose: bool = True, log: TextIO = sys.stderr) -> None:
        super(LocalPublicArchiveHttpConfig, self).__init__(siteId=siteId, verbose=verbose, log=log)
        self._protocol = "http"
        self._http_server = "files.wwpdb.org"
        self._http_server_prefix = "/pub"
