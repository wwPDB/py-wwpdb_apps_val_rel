##
#
# File:    ValConfig.py
# Author:  E. Peisach
# Date:    15-Dev-2019
# Updates:
#
##
"""
Contains settings pertinent to configuring the behaviour of the Validation Services
"""
from wwpdb.utils.config.ConfigInfo import ConfigInfo, getSiteId


class ValConfig(object):
    def __init__(self, site_id=None):
        if site_id is None:
            site_id = getSiteId()
        self.__site_id = site_id
        self.__cI = ConfigInfo(self.__site_id)

    @property
    def queue_name(self):
        return "val_release_queue_{}".format(self.__site_id)

    @property
    def routing_key(self):
        return "val_release_requests_{}".format(self.__site_id)

    @property
    def exchange(self):
        return "val_release_exchange_{}".format(self.__site_id)

    @property
    def ftp_server(self):
        server = self.__cI.get('SITE_FTP_SERVER') if self.__cI.get('SITE_FTP_SERVER') else 'ftp.wwpdb.org'
        return server

    @property
    def ftp_prefix(self):
        prefix = self.__cI.get('SITE_FTP_SERVER_PREFIX') if self.__cI.get('SITE_FTP_SERVER_PREFIX') else 'pub'
        return prefix

    @property
    def session_path(self):
        return self.__cI.get("SITE_WEB_APPS_SESSIONS_PATH")

    @property
    def val_cut_off(self):
        return self.__cI.get("PROJECT_VAL_REL_CUTOFF")
