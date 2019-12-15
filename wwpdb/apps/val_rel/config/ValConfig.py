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
    # Exchange queue names
    queue_name = "val_release_queue"
    routing_key = "val_release_requests"
    exchange = "val_release_exchange"

