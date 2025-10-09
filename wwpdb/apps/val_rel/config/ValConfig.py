##
#
# File:    ValConfig.py
# Author:  E. Peisach
# Date:    15-Dev-2019
# Updates: James Smith 7/2024
#
##
"""
Contains settings pertinent to configuring the behaviour of the Validation Services
"""
from wwpdb.utils.config.ConfigInfo import ConfigInfo, getSiteId
from wwpdb.utils.config.ConfigInfoApp import ConfigInfoAppCommon
import logging

class ValConfig(object):
    def __init__(self, site_id=None):
        if site_id is None:
            site_id = getSiteId()
        self.__site_id = site_id
        self.__cI = ConfigInfo(self.__site_id)
        self.__cICommon = ConfigInfoAppCommon(self.__site_id)
        self._val_rel_protocol = self.__cI.get('VAL_REL_PROTOCOL', 'http')
        if self._val_rel_protocol not in ['ftp', 'http', 'https']:
            logging.warning('Error - invalid protocol %s, setting to http' % self._val_rel_protocol)
            self._val_rel_protocol = 'http'
        # http settings
        self.connection_timeout = 60
        self.read_timeout = 60
        self.retries = 3
        self.backoff_factor = 15
        self.status_force_list = [429, 500, 502, 503, 504]
        # interval in seconds
        self._email_interval = 60 * 60 * 24
        # max number of emails per recipient within the interval
        self._max_per_interval = 10

    @property
    def val_rel_protocol(self):
        return self._val_rel_protocol

    @property
    def queue_name(self):
        message_queue = self.__cI.get('SITE_MESSAGE_QUEUE')
        queue_name = message_queue if message_queue else 'val_release_queue_{}'.format(self.__site_id)
        return queue_name

    @property
    def routing_key(self):
        return "val_release_requests_{}".format(self.__site_id)

    @property
    def exchange(self):
        return "val_release_exchange_{}".format(self.__site_id)

    @property
    def http_server(self):
        server = self.__cI.get('SITE_HTTP_SERVER', "files.wwpdb.org")
        return server

    @property
    def ftp_server(self):
        server = self.__cI.get('SITE_FTP_SERVER') if self.__cI.get('SITE_FTP_SERVER') else 'ftp.wwpdb.org'
        return server

    @property
    def http_prefix(self):
        prefix = self.__cI.get('SITE_HTTP_SERVER_PREFIX', '/pub')
        return prefix

    @property
    def ftp_prefix(self):
        prefix = self.__cI.get('SITE_FTP_SERVER_PREFIX') if self.__cI.get('SITE_FTP_SERVER_PREFIX') else '/pub'
        return prefix

    @property
    def session_path(self):
        return self.__cICommon.get_site_web_apps_sessions_path()

    @property
    def top_session_path(self):
        return self.__cICommon.get_site_web_apps_top_sessions_path()

    @property
    def val_cut_off(self):
        return self.__cI.get("PROJECT_VAL_REL_CUTOFF")


    @property
    def val_admin_email(self):
        """Returns list of email admin addresses as a list"""
        elist =  self.__cI.get("VAL_REL_ADMIN_EMAIL", None)
        if elist is None:
            return []
        return elist.split(",")

    @property
    def val_disable_multithread(self):
        """Returns True if the desire is to disable parallel invocation of validation"""
        value = True if self.__cI.get("VAL_REL_DISABLE_MULTITHREAD") else False
        return value
