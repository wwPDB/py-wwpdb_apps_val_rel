"""
Class to manage a state dictionary for validation runs.  Session state file is based on entryid
"""

import logging
import os
from typing import Dict, cast

from wwpdb.utils.ws_utils.ServiceDataStore import ServiceDataStore

logger = logging.getLogger()


class ValDataStore:
    def __init__(self, entryid: str, sessiondir: str):
        self.__sessiondir = sessiondir
        self.__sds = ServiceDataStore(self.__sessiondir, entryid)
        # Create empty state if does not exist
        fpath = self.__sds.getFilePath()
        if not os.path.exists(fpath):
            self.setValidationRunning(False)
        logger.debug("Session file %s", fpath)

    def getDictionary(self) -> Dict[str, str]:
        return cast("Dict[str, str]", self.__sds.getDictionary())

    def isValidationRunning(self) -> bool:
        """Returns True is a validation report generation is running"""
        val = self.__sds.get("status")
        if val == "running":
            return True
        return False

    def setValidationRunning(self, state: bool) -> bool:
        """Sets the status of if a validation run is in action"""
        if state:
            val = "running"
        else:
            val = "idle"
        return cast("bool", self.__sds.set("status", val, overWrite=True))
