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

class ValConfig(object):
    def __init__(self, siteID):
        self.__siteID = siteID

    @property
    def queue_name(self):
        return "val_release_queue"

    @property
    def routing_key(self):
        return "val_release_requests"

    @property
    def exchange(self):
        return "val_release_exchange"

