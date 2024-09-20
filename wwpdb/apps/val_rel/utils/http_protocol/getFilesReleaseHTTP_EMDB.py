# Retrieves EMDB files using http protocol
# Note, if local ftp tree is configured, it will use this instead of http protocol

import os
import logging
from wwpdb.apps.val_rel.config.ValConfig import ValConfig
from wwpdb.apps.val_rel.utils.http_protocol.getRemoteFilesHTTP import GetRemoteFilesHttp, setup_local_temp_http, remove_local_temp_http
from wwpdb.io.locator.ReleaseFileNames import ReleaseFileNames
from wwpdb.io.locator.localFTPPathInfo import LocalFTPPathInfo
from wwpdb.utils.config.ConfigInfo import getSiteId

logger = logging.getLogger(__name__)


class getFilesReleaseHttpEMDB(object):
    def __init__(self, emdbid, site_id=getSiteId(), local_ftp_emdb_path=None, cache=None):
        self.__site_id = site_id
        self.__rf = ReleaseFileNames()
        # __local_ftp is access to local ftp tree as a fallback
        self.__local_ftp = LocalFTPPathInfo()
        self.__local_ftp_emdb_path = local_ftp_emdb_path if local_ftp_emdb_path else self.__local_ftp.get_ftp_emdb()
        self.__temp_local_ftp = None
        self.__cache = cache

        vc = ValConfig(self.__site_id)
        self.__server = vc.http_server

        http_prefix = vc.http_prefix
        self.__session_path = vc.session_path
        protocol = vc.val_rel_protocol
        self.url_prefix = "%s://%s%s" % (protocol, self.__server, http_prefix)

        l_ftp = LocalFTPPathInfo()
        # This is probably wrong -- local file path
        l_ftp.set_ftp_emdb_root(self.url_prefix)
        self.url_prefix = l_ftp.get_ftp_emdb()
        self.__emdb_id = emdbid
        self.__grf = None
        if not self.__local_ftp.get_ftp_emdb():
            self.__grf = GetRemoteFilesHttp(server=self.__server, cache=self.__cache, site_id=self.__site_id)

    def get_emdb_xml(self):
        logger.info('EM XML')
        local_ftp = self.__local_ftp.get_ftp_emdb()
        logger.debug('local FTP path: "{}"'.format(local_ftp))
        if not local_ftp:
            logger.info('trying remote HTTP')
            self.__setup_local_temp_http()
            xml_file_name = self.__rf.get_emdb_xml(self.__emdb_id)
            url = os.path.join(self.url_prefix, self.__emdb_xml_folder(), xml_file_name)
            # subf = os.path.basename(self.__emdb_xml_folder())
            temp_file_path = self.__get_file_from_remote_http(url=url, subfolder=self.__emdb_xml_folder())
            if not temp_file_path:
                logger.info("removing temp file path")
                remove_local_temp_http(self.__setup_local_temp_http(), require_empty=True)
        else:
            logger.info('trying local FTP')
            temp_file_path = self.__get_emdb_local_ftp_file(filename=self.__rf.get_emdb_xml(self.__emdb_id),
                                                            emdb_path=self.__emdb_xml_folder())
        logger.info('returning: {}'.format(temp_file_path))
        return temp_file_path

    def get_emdb_fsc(self):
        logger.debug('FSC')
        local_ftp = self.__local_ftp.get_ftp_emdb()
        logger.debug('local FTP path: "{}"'.format(local_ftp))
        if not local_ftp:
            self.__setup_local_temp_http()
            logger.debug('trying remote HTTP')
            fsc_file_name = self.__rf.get_emdb_fsc(self.__emdb_id)
            url = os.path.join(self.url_prefix, self.__emdb_fsc_folder(), fsc_file_name)
            temp_file_path = self.__get_file_from_remote_http(url=url, subfolder=self.__emdb_fsc_folder())
            if not temp_file_path:
                remove_local_temp_http(self.__setup_local_temp_http(), require_empty=True)
        else:
            logger.debug('trying local FTP')
            temp_file_path = self.__get_emdb_local_ftp_file(filename=self.__rf.get_emdb_fsc(self.__emdb_id),
                                                            emdb_path=self.__emdb_fsc_folder())
        logger.debug('returning: {}'.format(temp_file_path))
        return temp_file_path

    def get_emdb_volume(self):
        logger.debug('em volume')
        local_ftp = self.__local_ftp.get_ftp_emdb()
        logger.debug('local FTP path: "{}"'.format(local_ftp))
        if not local_ftp:
            # In FTP access model -- this is supposed to pull in whole directory tree
            self.__setup_local_temp_http()
            logger.debug('trying remote HTTP')
            vol_file_name = self.__rf.get_emdb_map(self.__emdb_id)
            url = os.path.join(self.url_prefix, self.__emdb_map_folder(), vol_file_name)
            temp_file_path = self.__get_file_from_remote_http(url=url, subfolder=self.__emdb_map_folder())

            # Retreve other files that are required for validation
            self.get_emdb_half_maps()
            self.get_emdb_masks()
            if not temp_file_path:
                remove_local_temp_http(self.__setup_local_temp_http(), require_empty=True)
        else:
            logger.debug('trying local FTP')
            temp_file_path = self.__get_emdb_local_ftp_file(filename=self.__rf.get_emdb_map(self.__emdb_id),
                                                            emdb_path=self.__emdb_map_folder())
        logger.debug('returning: {}'.format(temp_file_path))
        return temp_file_path

    # Public for testing
    def get_emdb_half_maps(self):
        logger.debug('retrieving half maps')
        vol_file_name = self.__rf.get_emdb_map(self.__emdb_id)
        vol_file_name = vol_file_name.replace(".gz", "")
        half_map_name = vol_file_name.replace(".map", "_half_map.map")
        map_1_name = half_map_name.replace("_map", "_map_1")
        map_2_name = half_map_name.replace("_map", "_map_2")
        half_maps = [map_1_name, map_2_name]
        temp_file_paths = []
        if self.__grf is None:
            self.__grf = GetRemoteFilesHttp(server=self.__server, cache=self.__cache, site_id=self.__site_id)
        for half_map in half_maps:
            url = os.path.join(self.url_prefix, self.__emdb_half_map_folder(), half_map)
            temp_file_path = None
            if self.__grf.is_file(url):
                temp_file_path = self.__get_file_from_remote_http(url=url, subfolder=self.__emdb_half_map_folder())
            else:
                url += ".gz"
                if self.__grf.is_file(url):
                    temp_file_path = self.__get_file_from_remote_http(url=url, subfolder=self.__emdb_half_map_folder())
            temp_file_paths.append(temp_file_path)
        return temp_file_paths[0], temp_file_paths[1]

    def get_emdb_masks(self):
        logger.debug('retrieving masks')
        vol_file_name = self.__rf.get_emdb_map(self.__emdb_id)
        vol_file_name = vol_file_name.replace(".gz", "")
        mask_name = vol_file_name.replace(".map", "_msk.map")
        if self.__grf is None:
            self.__grf = GetRemoteFilesHttp(server=self.__server, cache=self.__cache, site_id=self.__site_id)
        # set max number to prevent inf loop
        max_masks = 100
        temp_file_paths = []
        for x in range(1, max_masks + 1):
            mask_file_name = mask_name.replace("_msk", "_msk_%d" % x)
            url = os.path.join(self.url_prefix, self.__emdb_mask_folder(), mask_file_name)
            temp_file_path = None
            if self.__grf.is_file(url):
                temp_file_path = self.__get_file_from_remote_http(url=url, subfolder=self.__emdb_mask_folder())
            else:
                url += ".gz"
                if self.__grf.is_file(url):
                    temp_file_path = self.__get_file_from_remote_http(url=url, subfolder=self.__emdb_mask_folder())
            if temp_file_path is None:
                break
            temp_file_paths.append(temp_file_path)

        return temp_file_paths

    def __setup_local_temp_http(self, session_path=None):
        if not self.__temp_local_ftp:
            if not session_path:
                session_path = self.__session_path
            self.__temp_local_ftp = setup_local_temp_http(temp_dir=self.__temp_local_ftp,
                                                          suffix=self.__emdb_id,
                                                          session_path=session_path
                                                      )
        return self.__temp_local_ftp

    def __emdb_xml_folder(self):
        """ Returns path in public archive to header subdir """
        return self.__get_emdb_subfolder(sub_folder='header')

    def __emdb_map_folder(self):
        """ Returns path in public archive to mao subdir """
        return self.__get_emdb_subfolder(sub_folder='map')

    def __emdb_fsc_folder(self):
        """ Returns path in public archive to fsc subdir """
        return self.__get_emdb_subfolder(sub_folder='fsc')

    def __emdb_half_map_folder(self):
        return self.__get_emdb_subfolder(sub_folder='other')

    def __emdb_mask_folder(self):
        return self.__get_emdb_subfolder(sub_folder='masks')

    def __get_emdb_subfolder(self, sub_folder):
        """ Generic returns sub_folder in public archive layout"""
        return os.path.join(self.__emdb_id, sub_folder)

    def __get_file_from_remote_http(self, *, url=None, subfolder=None):
        """
        gets file from HTTP site
        :return string: file name if it exists or None if it doesn't
        """
        logger.debug('get remote file from {}'.format(url))

        if self.__grf is None:
            self.__grf = GetRemoteFilesHttp(server=self.__server, cache=self.__cache, site_id=self.__site_id)
        outpath = os.path.join(self.__get_temp_local_ftp_emdb_path(), subfolder)
        ret = self.__grf.get_url(url=url, output_path=outpath)
        logger.debug(ret)
        if ret:
            # ret does not have subfolder name
            subfolder_path = os.path.join(subfolder, ret)
            return self.__get_emdb_local_http_single_file(filename=subfolder_path)
        return None

    def __get_temp_local_ftp_emdb_path(self):
        return os.path.join(self.__setup_local_temp_http(), self.__emdb_id)

    def __get_emdb_local_http_single_file(self, filename):
        """ If file retrieved, store it """
        if os.path.exists(self.__get_temp_local_ftp_emdb_path()):
            temp_file_path = os.path.join(self.__get_temp_local_ftp_emdb_path(), filename)
            if os.path.exists(temp_file_path):
                return temp_file_path
        return None

    def __get_emdb_local_ftp_file(self, emdb_path, filename):
        """ Retrieves file from local copy of ftp tree """
        local_ftp = self.__get_local_emdb_subfolder(emdb_path=emdb_path)
        if local_ftp:
            file_path = os.path.join(local_ftp, filename)
            if os.path.exists(file_path):
                return file_path
        return None

    def __get_local_emdb_subfolder(self, emdb_path):
        if self.__local_ftp_emdb_path:
            return os.path.join(self.__local_ftp_emdb_path, emdb_path)
        return None

    def remove_local_temp_files(self):
        """Cleanup of local download diretcory if present"""
        logger.debug("Cleaning up HTTP EMDB local directory %s", self.__temp_local_ftp)
        if self.__temp_local_ftp and os.path.exists(self.__temp_local_ftp):
            remove_local_temp_http(self.__temp_local_ftp, require_empty=False)

    def close_connection(self):
        # maintained for backward compatibility with ftp version
        if self.__grf is not None:
            self.__grf.disconnect()
            self.__grf = None
