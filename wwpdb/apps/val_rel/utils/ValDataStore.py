"""
Class to manage a state dictionary for validation runs.  Session state file is based on entryid
"""

import os
import logging
from wwpdb.utils.ws_utils.ServiceDataStore import ServiceDataStore

logger = logging.getLogger()


class ValDataStore(object):
    def __init__(self, entryid, sessiondir):
        self.__sessiondir = sessiondir
        self.__entryid = entryid
        self.__sds = ServiceDataStore(self.__sessiondir, entryid)
        # Create empty state if does not exist
        fpath = self.__sds.getFilePath()
        if not os.path.exists(fpath):
            self.setValidationRunning(False)
        logger.debug("Session file %s", fpath)

    def getDictionary(self):
        return self.__sds.getDictionary()

    def isValidationRunning(self):
        """Returns True is a validation report generation is running"""
        val = self.__sds.get('status')
        if val == "running":
            return True
        else:
            return False

    def setValidationRunning(self, state):
        """Sets the status of if a validation run is in action"""
        if state:
            val = "running"
        else:
            val = "idle"
        return self.__sds.set("status", val, overWrite=True)
