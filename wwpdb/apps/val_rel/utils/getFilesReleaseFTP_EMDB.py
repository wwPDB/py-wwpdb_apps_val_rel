import logging
import os

from wwpdb.apps.val_rel.config.ValConfig import ValConfig
from wwpdb.apps.val_rel.utils.getRemoteFilesFTP import GetRemoteFiles, setup_local_temp_ftp, remove_local_temp_ftp
from wwpdb.io.locator.ReleaseFileNames import ReleaseFileNames
from wwpdb.io.locator.localFTPPathInfo import LocalFTPPathInfo
from wwpdb.utils.config.ConfigInfo import getSiteId

logger = logging.getLogger(__name__)


class getFilesReleaseFtpEMDB(object):
    def __init__(self, emdbid, site_id=getSiteId(), local_ftp_emdb_path=None):
        self.__site_id = site_id
        self.__rf = ReleaseFileNames()
        self.__local_ftp = LocalFTPPathInfo()
        self.__local_ftp_emdb_path = local_ftp_emdb_path if local_ftp_emdb_path else self.__local_ftp.get_ftp_emdb()
        self.__temp_local_ftp = None
        vc = ValConfig(self.__site_id)
        self.server = vc.ftp_server
        self.session_path = vc.session_path
        site_url_prefix = vc.ftp_prefix
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
                session_path = self.session_path
            self.__temp_local_ftp = setup_local_temp_ftp(temp_dir=self.__temp_local_ftp,
                                                         suffix=self.emdb_id,
                                                         session_path=session_path
                                                         )
        return self.__temp_local_ftp

    def remove_local_temp_files(self):
        """Cleanup of local ftp diretcory if present"""

        logger.debug("Cleaning up FTP EMDB local directory %s", self.__temp_local_ftp)
        if self.__temp_local_ftp and os.path.exists(self.__temp_local_ftp):
            remove_local_temp_ftp(self.__temp_local_ftp, require_empty=False)

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

    def get_emdb_local_ftp_single_file(self, filename):
        if os.path.exists(self.get_temp_local_ftp_emdb_path()):
            file_path = os.path.join(self.get_temp_local_ftp_emdb_path(), filename)
            if os.path.exists(file_path):
                return file_path
        return None

    def get_remote_ftp_data(self):
        ok = self.get_emdb_from_remote_ftp()
        if ok:
            self.set_temp_local_ftp_as_local_ftp_path()
            return True
        else:
            remove_local_temp_ftp(self.setup_local_temp_ftp(), require_empty=True)

    def get_emdb_xml(self):
        logger.debug('em XML')
        if self.__local_ftp.get_ftp_emdb():
            logger.debug('trying local FTP')
            file_name = self.get_emdb_local_ftp_file(filename=self.__rf.get_emdb_xml(self.emdb_id),
                                                     emdb_path=self.emdb_xml_folder())
        else:
            logger.debug('trying remote FTP')
            self.setup_local_temp_ftp()
            file_name = self.get_file_from_remote_ftp(filename=self.__rf.get_emdb_xml(self.emdb_id),
                                                      file_path=os.path.join(self.url_prefix, self.emdb_xml_folder()))

            if not file_name:
                remove_local_temp_ftp(self.setup_local_temp_ftp(), require_empty=True)
        logger.debug('returning: {}'.format(file_name))
        return file_name

    def get_emdb_volume(self):
        logger.debug('em volume')
        if self.__local_ftp.get_ftp_emdb():
            logger.debug('trying local FTP')
            file_name = self.get_emdb_local_ftp_file(filename=self.__rf.get_emdb_map(self.emdb_id),
                                                     emdb_path=self.emdb_map_folder())
        else:
            logger.debug('trying remote FTP')
            self.get_remote_ftp_data()
            file_name = self.get_emdb_local_ftp_file(filename=self.__rf.get_emdb_map(self.emdb_id),
                                                     emdb_path=self.emdb_map_folder())
        logger.debug('returning: {}'.format(file_name))
        return file_name

    def get_emdb_fsc(self):
        logger.debug('FSC')
        if self.__local_ftp.get_ftp_emdb():
            logger.debug('trying local FTP')
            file_name = self.get_emdb_local_ftp_file(filename=self.__rf.get_emdb_fsc(self.emdb_id),
                                                     emdb_path=self.emdb_fsc_folder())
        else:
            self.setup_local_temp_ftp()
            logger.debug('trying remote FTP')
            file_name = self.get_file_from_remote_ftp(filename=self.__rf.get_emdb_fsc(self.emdb_id),
                                                      file_path=os.path.join(self.url_prefix, self.emdb_fsc_folder()))
            if not file_name:
                remove_local_temp_ftp(self.setup_local_temp_ftp(), require_empty=True)
        logger.debug('returning: {}'.format(file_name))
        return file_name

    def check_header_on_remote_ftp(self):
        """
        checks if an EMDB header exists of the FTP site
        :return: True if it exists, False if it fails
        """
        logger.debug('check EMDB header from remote FTP')
        url_directory = os.path.join(self.url_prefix, self.emdb_xml_folder())
        filename = self.__rf.get_emdb_xml(self.emdb_id)
        ret = self.get_file_from_remote_ftp(file_path=url_directory, filename=filename)
        logger.debug(ret)
        if ret:
            return True
        return False

    def get_emdb_from_remote_ftp(self):
        """
        Get the full EMDB FTP directory from the FTP site if it exists
        :return: True if ok, False if either does not exist or failed
        """
        logger.debug('getting EMDB from remote FTP')
        ok = self.check_header_on_remote_ftp()
        if ok:
            logger.debug('header found on remote FTP')
            url_directory = os.path.join(self.url_prefix, self.emdb_id)
            grf = GetRemoteFiles(server=self.server, output_path=self.get_temp_local_ftp_emdb_path())
            ret = grf.get_directory(directory=url_directory)
            logger.debug(ret)
            if ret:
                return True
        return False

    def get_file_from_remote_ftp(self, file_path, filename):
        """
        gets file from FTP site
        :return string: file name if it exists or None if it doesn't
        """
        logger.debug('get remote file {} FTP from {}'.format(filename, file_path))
        grf = GetRemoteFiles(server=self.server, output_path=self.get_temp_local_ftp_emdb_path())
        ret = grf.get_url(directory=file_path, filename=filename)
        logger.debug(ret)
        if ret:
            return self.get_emdb_local_ftp_single_file(filename=ret[0])
        return None

