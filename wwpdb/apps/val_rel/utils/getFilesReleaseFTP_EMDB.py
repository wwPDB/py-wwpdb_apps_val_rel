import logging
import os
import tempfile

from wwpdb.io.locator.ReleaseFileNames import ReleaseFileNames
from wwpdb.io.locator.localFTPPathInfo import LocalFTPPathInfo
from wwpdb.utils.config.ConfigInfo import ConfigInfo, getSiteId

from wwpdb.apps.val_rel.utils.getRemoteFilesFTP import GetRemoteFiles

logger = logging.getLogger(__name__)


class getFilesReleaseFtpEMDB:
    def __init__(self, emdbid, site_id=getSiteId(), local_ftp_emdb_path=None):
        self.__site_id = site_id
        self.__cI = ConfigInfo(self.__site_id)
        self.__rf = ReleaseFileNames()
        self.__local_ftp = LocalFTPPathInfo()
        self.__local_ftp_emdb_path = local_ftp_emdb_path if local_ftp_emdb_path else self.__local_ftp.get_ftp_emdb()
        self.__temp_local_ftp = None
        self.server = self.__cI.get('SITE_FTP_SERVER')
        site_url_prefix = self.__cI.get('SITE_FTP_SERVER_PREFIX')
        l_ftp = LocalFTPPathInfo()
        l_ftp.set_ftp_emdb_root(site_url_prefix)
        self.url_prefix = l_ftp.get_ftp_emdb()
        self.emdb_id = emdbid

    def get_emdb_subfolder(self, sub_folder):
        return os.path.join(self.emdb_id, sub_folder)

    def emdb_xml_folder(self):
        return self.get_emdb_subfolder(sub_folder='header')

    def emdb_map_folder(self, ):
        return self.get_emdb_subfolder(sub_folder='map')

    def emdb_fsc_folder(self):
        return self.get_emdb_subfolder(sub_folder='fsc')

    def setup_local_temp_ftp(self, session_path=None):
        if not self.__temp_local_ftp:
            if not session_path:
                session_path = self.__cI.get("SITE_WEB_APPS_SESSIONS_PATH")
            if not os.path.exists(session_path):
                os.makedirs(session_path)
            self.__temp_local_ftp = tempfile.mkdtemp(
                dir=session_path,
                prefix="ftp_{}".format(self.emdb_id)
            )
        return self.__temp_local_ftp

    def set_temp_local_ftp_as_local_ftp_path(self):
        self.setup_local_temp_ftp()
        self.__local_ftp_emdb_path = self.__temp_local_ftp

    def get_temp_local_ftp_emdb_path(self):
        return os.path.join(self.setup_local_temp_ftp(), self.emdb_id)

    def get_local_emdb_subfolder(self, emdb_path):
        if self.__local_ftp_emdb_path:
            return os.path.join(self.__local_ftp_emdb_path, emdb_path)
        return None

    def get_emdb_local_ftp_file(self, emdb_path, filename):
        local_ftp = self.get_local_emdb_subfolder(emdb_path=emdb_path)
        if local_ftp:
            file_path = os.path.join(local_ftp, filename)
            if os.path.exists(file_path):
                return file_path
        return None

    def get_remote_ftp_data(self):
        if not os.path.exists(self.get_temp_local_ftp_emdb_path()):
            ok = self.get_emdb_from_remote_ftp()
            if ok:
                self.set_temp_local_ftp_as_local_ftp_path()

    def get_emdb_xml(self):
        file_name = self.get_emdb_local_ftp_file(filename=self.__rf.get_emdb_xml(self.emdb_id),
                                                 emdb_path=self.emdb_xml_folder())
        if not file_name:
            self.get_remote_ftp_data()
            file_name = self.get_emdb_local_ftp_file(filename=self.__rf.get_emdb_xml(self.emdb_id),
                                                     emdb_path=self.emdb_xml_folder())
        return file_name

    def get_emdb_volume(self):
        file_name = self.get_emdb_local_ftp_file(filename=self.__rf.get_emdb_map(self.emdb_id),
                                                 emdb_path=self.emdb_map_folder())
        if not file_name:
            self.get_remote_ftp_data()
            file_name = self.get_emdb_local_ftp_file(filename=self.__rf.get_emdb_map(self.emdb_id),
                                                     emdb_path=self.emdb_map_folder())
        return file_name

    def get_emdb_fsc(self):
        file_name = self.get_emdb_local_ftp_file(filename=self.__rf.get_emdb_fsc(self.emdb_id),
                                                 emdb_path=self.emdb_fsc_folder())
        if not file_name:
            self.get_remote_ftp_data()
            file_name = self.get_emdb_local_ftp_file(filename=self.__rf.get_emdb_fsc(self.emdb_id),
                                                     emdb_path=self.emdb_fsc_folder())
        return file_name

    def check_header_on_remote_ftp(self):
        """
        checks if an EMDB header exists of the FTP site
        :return: True if it exists, False if it fails
        """
        url_directory = os.path.join(self.url_prefix, self.emdb_xml_folder())
        filename = self.__rf.get_emdb_xml(self.emdb_id)
        grf = GetRemoteFiles(server=self.server, output_path=self.get_temp_local_ftp_emdb_path())
        ret = grf.get_url(directory=url_directory, filename=filename)
        print(ret)
        if ret:
            return True
        return False

    def get_emdb_from_remote_ftp(self):
        """
        Get the full EMDB FTP directory from the FTP site if it exists
        :return: True if ok, False if either does not exist or failed
        """
        ok = self.check_header_on_remote_ftp()
        if ok:
            url_directory = os.path.join(self.url_prefix, self.emdb_id)
            grf = GetRemoteFiles(server=self.server, output_path=self.get_temp_local_ftp_emdb_path())
            ret = grf.get_directory(directory=url_directory)
            if ret:
                return True
        return False
