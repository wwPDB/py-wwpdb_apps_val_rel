import os
import logging
from wwpdb.apps.val_rel.config.ValConfig import ValConfig
from wwpdb.apps.val_rel.http.getRemoteFilesHTTP import GetRemoteFiles, setup_local_temp_ftp, remove_local_temp_ftp
from wwpdb.io.locator.ReleaseFileNames import ReleaseFileNames
from wwpdb.io.locator.localFTPPathInfo import LocalFTPPathInfo
from wwpdb.utils.config.ConfigInfo import getSiteId

logger = logging.getLogger(__name__)


class getFilesReleaseHttpEMDB(object):
    def __init__(self, emdbid, site_id=getSiteId(), local_ftp_emdb_path=None, cache=None):
        self.__site_id = site_id
        self.__rf = ReleaseFileNames()
        self.__local_ftp = LocalFTPPathInfo()
        self.__local_ftp_emdb_path = local_ftp_emdb_path if local_ftp_emdb_path else self.__local_ftp.get_ftp_emdb()
        self.__temp_local_ftp = None
        self.__cache = cache
        vc = ValConfig(self.__site_id)
        self.server = vc.http_server
        self.ftp_prefix = vc.http_prefix
        self.session_path = vc.session_path
        protocol = vc.val_rel_protocol
        self.url_prefix = "%s://%s%s" % (protocol, self.server, self.ftp_prefix)
        l_ftp = LocalFTPPathInfo()
        l_ftp.set_ftp_emdb_root(self.url_prefix)
        self.url_prefix = l_ftp.get_ftp_emdb()
        self.emdb_id = emdbid
        self.grf = None
        if not self.__local_ftp.get_ftp_emdb():
            self.grf = GetRemoteFiles(server=self.server, cache=self.__cache)

    def get_emdb_xml(self):
        logger.info('EM XML')
        local_ftp = self.__local_ftp.get_ftp_emdb()
        logger.debug('local FTP path: "{}"'.format(local_ftp))
        if not local_ftp:
            logger.info('trying remote FTP')
            self.setup_local_temp_ftp()
            xml_file_name = self.__rf.get_emdb_xml(self.emdb_id)
            url = os.path.join(self.url_prefix, self.emdb_xml_folder(), xml_file_name)
            # subf = os.path.basename(self.emdb_xml_folder())
            temp_file_path = self.get_file_from_remote_ftp(url=url, subfolder=self.emdb_xml_folder())
            if not temp_file_path:
                logger.info("removing temp file path")
                remove_local_temp_ftp(self.setup_local_temp_ftp(), require_empty=True)
        else:
            logger.info('trying local FTP')
            temp_file_path = self.get_emdb_local_ftp_file(filename=self.__rf.get_emdb_xml(self.emdb_id),
                                                     emdb_path=self.emdb_xml_folder())
        logger.info('returning: {}'.format(temp_file_path))
        return temp_file_path

    def get_emdb_fsc(self):
        logger.debug('FSC')
        local_ftp = self.__local_ftp.get_ftp_emdb()
        logger.debug('local FTP path: "{}"'.format(local_ftp))
        if not local_ftp:
            self.setup_local_temp_ftp()
            logger.debug('trying remote FTP')
            fsc_file_name = self.__rf.get_emdb_fsc(self.emdb_id)
            url = os.path.join(self.url_prefix, self.emdb_fsc_folder(), fsc_file_name)
            temp_file_path = self.get_file_from_remote_ftp(url=url, subfolder=self.emdb_fsc_folder())
            if not temp_file_path:
                remove_local_temp_ftp(self.setup_local_temp_ftp(), require_empty=True)
        else:
            logger.debug('trying local FTP')
            temp_file_path = self.get_emdb_local_ftp_file(filename=self.__rf.get_emdb_fsc(self.emdb_id),
                                                     emdb_path=self.emdb_fsc_folder())
        logger.debug('returning: {}'.format(temp_file_path))
        return temp_file_path

    def get_emdb_volume(self):
        logger.debug('em volume')
        local_ftp = self.__local_ftp.get_ftp_emdb()
        logger.debug('local FTP path: "{}"'.format(local_ftp))
        if not local_ftp:
            self.setup_local_temp_ftp()
            logger.debug('trying remote FTP')
            vol_file_name = self.__rf.get_emdb_map(self.emdb_id)
            url = os.path.join(self.url_prefix, self.emdb_map_folder(), vol_file_name)
            temp_file_path = self.get_file_from_remote_ftp(url=url, subfolder=self.emdb_map_folder())
            if not temp_file_path:
                remove_local_temp_ftp(self.setup_local_temp_ftp(), require_empty=True)
        else:
            logger.debug('trying local FTP')
            temp_file_path = self.get_emdb_local_ftp_file(filename=self.__rf.get_emdb_map(self.emdb_id),
                                                     emdb_path=self.emdb_map_folder())
        logger.debug('returning: {}'.format(temp_file_path))
        return temp_file_path

    def setup_local_temp_ftp(self, session_path=None):
        if not self.__temp_local_ftp:
            if not session_path:
                session_path = self.session_path
            self.__temp_local_ftp = setup_local_temp_ftp(temp_dir=self.__temp_local_ftp,
                                                         suffix=self.emdb_id,
                                                         session_path=session_path
                                                         )
        return self.__temp_local_ftp

    def emdb_xml_folder(self):
        return self.get_emdb_subfolder(sub_folder='header')

    def emdb_map_folder(self):
        return self.get_emdb_subfolder(sub_folder='map')

    def emdb_fsc_folder(self):
        return self.get_emdb_subfolder(sub_folder='fsc')

    def get_emdb_subfolder(self, sub_folder):
        return os.path.join(self.emdb_id, sub_folder)

    def get_file_from_remote_ftp(self, *, url=None, subfolder=None):
        """
        gets file from FTP site
        :return string: file name if it exists or None if it doesn't
        """
        logger.debug('get remote file from {}'.format(url))

        if self.grf is None:
            self.grf = GetRemoteFiles(server=self.server, cache=self.__cache)
        outpath = os.path.join(self.get_temp_local_ftp_emdb_path(), subfolder)
        ret = self.grf.get_url(url=url, output_path=outpath)
        logger.debug(ret)
        if ret:
            # ret does not have subfolder name
            subfolder_path = os.path.join(subfolder, ret)
            return self.get_emdb_local_ftp_single_file(filename=subfolder_path)
        return None

    def get_temp_local_ftp_emdb_path(self):
        return os.path.join(self.setup_local_temp_ftp(), self.emdb_id)

    def get_emdb_local_ftp_single_file(self, filename):
        if os.path.exists(self.get_temp_local_ftp_emdb_path()):
            temp_file_path = os.path.join(self.get_temp_local_ftp_emdb_path(), filename)
            if os.path.exists(temp_file_path):
                return temp_file_path
        return None

    def get_emdb_local_ftp_file(self, emdb_path, filename):
        local_ftp = self.get_local_emdb_subfolder(emdb_path=emdb_path)
        if local_ftp:
            file_path = os.path.join(local_ftp, filename)
            if os.path.exists(file_path):
                return file_path
        return None

    def get_local_emdb_subfolder(self, emdb_path):
        if self.__local_ftp_emdb_path:
            return os.path.join(self.__local_ftp_emdb_path, emdb_path)
        return None

    def remove_local_temp_files(self):
        """Cleanup of local ftp diretcory if present"""
        logger.debug("Cleaning up FTP EMDB local directory %s", self.__temp_local_ftp)
        if self.__temp_local_ftp and os.path.exists(self.__temp_local_ftp):
            remove_local_temp_ftp(self.__temp_local_ftp, require_empty=False)

    def close_connection(self):
        # maintained for backward compatibility with ftp version
        if self.grf is not None:
            self.grf.disconnect()
            self.grf = None

    def set_temp_local_ftp_as_local_ftp_path(self):
        self.setup_local_temp_ftp()
        self.__local_ftp_emdb_path = self.__temp_local_ftp

    def get_local_ftp_path(self):
        return self.__local_ftp.get_ftp_emdb()

    def set_local_ftp_path(self, ftp_path):
        self.__local_ftp.set_ftp_emdb_root(ftp_path)
        self.__local_ftp_emdb_path = ftp_path

