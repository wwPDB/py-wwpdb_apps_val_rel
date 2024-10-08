import requests
from requests.adapters import HTTPAdapter
import urllib.parse
from urllib3.util.retry import Retry, MaxRetryError
import logging
import os
import shutil
import tempfile
from wwpdb.apps.val_rel.utils.PersistFileCache import PersistFileCache
from wwpdb.apps.val_rel.config.ValConfig import ValConfig
from wwpdb.apps.val_rel.utils.emailHandler import EmailHandler

logger = logging.getLogger(__name__)


def setup_local_temp_http(temp_dir, suffix, session_path):
    if not temp_dir:
        if not os.path.exists(session_path):
            os.makedirs(session_path)
        temp_dir = tempfile.mkdtemp(
            dir=session_path,
            prefix="http_{}_".format(suffix)
        )
    return temp_dir


def remove_local_temp_http(temp_dir, require_empty=False):
    """Removes the temporary directory. If require_empty true, will skip if not"""
    if temp_dir and os.path.exists(temp_dir):
        if require_empty:
            dlist = os.listdir(temp_dir)
            if len(dlist) > 0:
                logger.info("Skipping removal of %s as not empty", temp_dir)
                return
        shutil.rmtree(temp_dir, ignore_errors=True)


class GetRemoteFilesHttp(object):
    def __init__(self, server=None, cache=None, site_id=None):  # pylint: disable=unused-argument
        self.__cache = cache
        vc = ValConfig(site_id=site_id)
        self.connection_timeout = vc.connection_timeout
        self.read_timeout = vc.read_timeout
        self.__timeout = self.connection_timeout
        self.__retries = vc.retries
        self.__backoff_factor = vc.backoff_factor
        self.__status_force_list = vc.status_force_list
        self.emailHandler = EmailHandler(site_id)

    def get_url(self, *, url=None, output_path=None):
        """Retrieve file from url.  Note:  This is a little backwards - should check cache instead of waiting for get_file"""
        if not url:
            raise ValueError("url must be specified")

        # Old code would check is_file() - and then get_file. get_file checks cache before download so no need here to check remote if file. If we have it
        # cached, it is real.
        self.get_file(url, output_path)
        return os.path.basename(url)

    def is_file(self, remote_file):
        with requests.Session() as s:
            try:
                self.__mount_session_retry(s)
                r = s.head(remote_file, timeout=self.__timeout, allow_redirects=True)
                if r.status_code < 400 and r.headers and 'content-length' in r.headers and int(r.headers['content-length']) > 0:
                    return True
                return False
            except Exception as e:
                logging.error("Failure to get head of file %s %s", remote_file, e)
                # We re-raise the exception - as there is no other way to handle
                raise e


    def get_file(self, remote_file, output_path):
        """
        get from cache if found
        otherwise, download to temp dir in sessions path
        copy from temp dir to cache
        """

        self._setup_output_path(output_path)

        # output path = temp dir in sessions path
        temp_file_name = os.path.join(output_path, os.path.basename(remote_file))

        logger.debug("Transferring file %s to %s", remote_file, temp_file_name)
        logger.debug("Cache is %s", self.__cache)
        if self.__cache is not None:
            # See if in cache
            pfc = PersistFileCache(self.__cache)
            cache_file_path = os.path.join(self.__cache, urllib.parse.urlparse(remote_file).path)
            if pfc.exists(cache_file_path):
                # delete any temp file and replace with sym link from session dir to cache file
                pfc.get_file(cache_file_path, temp_file_name, symlink=True)
                logger.debug("Found %s in cache", cache_file_path)
                return
            logger.debug("Did not find %s in cache", remote_file)

        if self.is_file(remote_file):
            # download to temp dir in sessions path
            if self.httpRequest(remote_file, os.path.join(output_path, temp_file_name)):
                # copy from temp dir to cache
                if self.__cache is not None:
                    pfc.add_file(temp_file_name, cache_file_path)
                    logger.debug("Adding %s to cache", cache_file_path)

    def _setup_output_path(self, output_path):
        if not os.path.exists(output_path):
            os.makedirs(output_path)

    def __mount_session_retry(self, session):
        """Sets up retry for session"""
        retries = Retry(total=self.__retries, backoff_factor=self.__backoff_factor, status_forcelist=self.__status_force_list, allowed_methods=["GET"])
        session.mount('https://', HTTPAdapter(max_retries=retries))
        session.mount('http://', HTTPAdapter(max_retries=retries))

    def httpRequest(self, url, outfilepath):
        """ download to session directory """
        logging.info("http request for %s", url)
        status_code = -1
        with requests.Session() as s:
            self.__mount_session_retry(s)
            try:
                r = s.get(url, timeout=(self.connection_timeout, self.read_timeout), stream=True, allow_redirects=True)
            except MaxRetryError as _e:  # noqa: F841
                msg = "Max retries exceeded for %s" % os.path.basename(url)
                self.handle_exception(msg)
                return False
            except requests.exceptions.ConnectTimeout as _e:  # noqa: F841
                msg = "Connection timed out for %s" % os.path.basename(url)
                self.handle_exception(msg)
                return False
            except requests.exceptions.ConnectionError as _e:  # noqa: F841
                msg = "Connection error for %s" % os.path.basename(url)
                self.handle_exception(msg)
                return False
            except requests.exceptions.ReadTimeout as _e:  # noqa: F841
                msg = "Data reading timed out for %s" % os.path.basename(url)
                self.handle_exception(msg)
                return False
            except requests.exceptions.RequestException as _e:  # noqa: F841
                msg = "Request for %s failed with status code %d" % (os.path.basename(url), status_code)
                self.handle_exception(msg)
                return False
            except Exception as _e:  # noqa: F841
                msg = "Request for %s failed with status code %d" % (os.path.basename(url), status_code)
                self.handle_exception(msg)
                return False

            content_length = None
            if r is not None:
                status_code = r.status_code
                # does not return correct length for text files
                if r.headers and 'content-length' in r.headers:
                    content_length = int(r.headers['content-length'])
                logger.info("%s status code %d", os.path.basename(url), status_code)

            if 0 < status_code < 400:
                try:
                    with open(outfilepath, "wb") as w:
                        w.write(r.content)
                except requests.exceptions.ReadTimeout as _e:  # noqa: F841
                    msg = "Data reading timed out for %s" % os.path.basename(url)
                    self.handle_exception(msg)
                    if os.path.exists(outfilepath):
                        os.unlink(outfilepath)
                    return False
                filesize = os.path.getsize(outfilepath)
                if content_length is not None and filesize != content_length:
                    logger.warning("File size mismatch: %s != %s", filesize, content_length)
                logger.info("downloaded %s size %d", os.path.basename(url), filesize)
                return True
            else:
                msg = "Request for %s failed with status code %d" % (os.path.basename(url), status_code)
                self.handle_exception(msg)
                return False
        return False

    def handle_exception(self, msg):
        self.emailHandler.send_email_admins(msg)
        logger.exception(msg)


    def disconnect(self):
        # maintained for backward compatibility with ftp version
        pass
