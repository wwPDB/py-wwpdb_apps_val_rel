import os
import smtplib
import time
import shelve
from filelock import SoftFileLock
from email.message import EmailMessage
from wwpdb.utils.config.ConfigInfo import getSiteId
from wwpdb.utils.config.ConfigInfoApp import ConfigInfoAppCommunication
from wwpdb.apps.val_rel.config.ValConfig import ValConfig
from wwpdb.apps.val_rel.utils.outputFiles import outputFiles
import logging

logger = logging.getLogger(__name__)


class EmailHandler:

    def __init__(self, site_id=None):
        vc = ValConfig(site_id=site_id)
        self.__admin_list = vc.val_admin_email
        self.__email_interval = vc._email_interval
        self.__max_per_interval = vc._max_per_interval

        oF = outputFiles(siteID=site_id)
        self.__dir = oF.get_root_state_folder()
        logger.debug("email handler using directory %s", self.__dir)
        self.__shelf_file = os.path.join(self.__dir, "service.shelf")
        self.__lock_file = os.path.join(self.__dir, "service.lock")

    def send_email_admins(self, msg):
        for admin in self.__admin_list:
            self.send_email(msg, admin)

    def send_email(self, txt, recipient):
        if not os.path.exists(self.__dir):
            os.makedirs(self.__dir)
        lock = SoftFileLock(self.__lock_file)
        with lock:
            with shelve.open(self.__shelf_file) as db:
                if recipient not in db:
                    db[recipient] = "%d,%d" % (1, time.time())
                else:
                    tokens = db[recipient].split(",")
                    count = int(tokens[0])
                    msg_log_time = int(tokens[1])
                    # if haven't reached cutoff time
                    if msg_log_time + self.__email_interval > time.time():
                        # but sent too many emails already
                        if count >= self.__max_per_interval:
                            return
                        # still within grace period
                        count += 1
                        db[recipient] = "%d,%d" % (count, msg_log_time)
                    # otherwise reset values
                    else:
                        db[recipient] = "%d,%d" % (1, time.time())
        content = """
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
        except Exception:  # noqa: E722,BLE001
            logger.exception("unable to send to %s email %s", recipient, content)
