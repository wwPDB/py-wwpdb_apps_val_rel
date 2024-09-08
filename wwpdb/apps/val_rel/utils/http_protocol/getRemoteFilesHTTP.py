import requests
from requests.adapters import HTTPAdapter
import urllib.parse
from urllib3.util.retry import Retry, MaxRetryError
import smtplib
import logging
import os
import shutil
import tempfile
import time
from email.message import EmailMessage
from wwpdb.apps.val_rel.utils.PersistFileCache import PersistFileCache
from wwpdb.apps.val_rel.config.ValConfig import ValConfig
from wwpdb.utils.config.ConfigInfo import getSiteId
from wwpdb.utils.config.ConfigInfoApp import ConfigInfoAppCommunication

logger = logging.getLogger(__name__)


def setup_local_temp_http(temp_dir, suffix, session_path):
    if not temp_dir:
        if not os.path.exists(session_path):
            os.makedirs(session_path)
        temp_dir = tempfile.mkdtemp(
            dir=session_path,
            prefix="ftp_{}_".format(suffix)
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
    def __init__(self, server=None, cache=None):  # pylint: disable=unused-argument
        self.__cache = cache
        vc = ValConfig()
        self.connection_timeout = vc.connection_timeout
        self.read_timeout = vc.read_timeout
        self.__timeout = self.connection_timeout
        self.__retries = vc.retries
        self.__backoff_factor = vc.backoff_factor
        self.__status_force_list = vc.status_force_list
        self.__admin_list = vc._admin_list
        self.__email_interval = vc._email_interval
        self.__max_per_interval = vc._max_per_interval
        # warning - possible security risk
        # self.__ignore_certificate_on_last_try = False

    def get_url(self, *, url=None, output_path=None):
        if not url:
            raise ValueError("url must be specified")
        if self.is_file(url):
            self.get_file(url, output_path)
        return os.path.basename(url)

    def is_file(self, remote_file):
        r = requests.head(remote_file, timeout=self.__timeout, allow_redirects=True)
        if r.status_code < 400 and r.headers and 'content-length' in r.headers and int(r.headers['content-length']) > 0:
            return True
        return False

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

    def httpRequest(self, url, outfilepath):
        """ download to session directory """
        logging.info("http request for %s", url)
        status_code = -1
        with requests.Session() as s:
            retries = Retry(total=self.__retries, backoff_factor=self.__backoff_factor, status_forcelist=self.__status_force_list, allowed_methods=["GET"])
            s.mount('https://', HTTPAdapter(max_retries=retries))
            s.mount('http://', HTTPAdapter(max_retries=retries))
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
        for admin in self.__admin_list:
            self.send_email(msg, admin)
        logger.exception(msg)

    def send_email(self, txt, recipient):
        envar = os.getenv(recipient)
        if not envar:
            os.environ[recipient] = "%d,%d" % (1, time.time())
        else:
            tokens = envar.split(",")
            count = int(tokens[0])
            msg_log_time = int(tokens[1])
            if msg_log_time + self.__email_interval > time.time():
                if count >= self.__max_per_interval:
                    return
                count += 1
                os.environ[recipient] = "%d,%d" % (count, msg_log_time)
            else:
                os.environ[recipient] = "%d,%d" % (1, time.time())
        content = """\
        The Val Rel application at {site_id} threw an exception!
        The following error output was retrieved:
        {txt}""".format(site_id=getSiteId(), txt=txt)
        self.email(content, recipient)

    def email(self, content, recipient):
        app = ConfigInfoAppCommunication(siteId=getSiteId())
        server = app.get_mailserver_name()
        no_reply = app.get_noreply_address()
        msg = EmailMessage()
        msg.set_content(content)
        msg['Subject'] = "WWPDB Val Rel Exception"
        msg['From'] = no_reply
        msg['To'] = recipient
        try:
            with smtplib.SMTP(server) as s:
                s.send_message(msg)
        except Exception as _e:  # noqa: F841
            logger.exception("unable to send to %s email %s", recipient, content)

    def disconnect(self):
        # maintained for backward compatibility with ftp version
        pass
