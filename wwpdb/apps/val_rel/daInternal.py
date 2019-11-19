##
# File:  DaInternal.py
# Date:  1-Aug-2019  E. Peisach
#
# Updated:
#
#
"""
Wrapper for utilities for da_internal access.  Once DB is open, tries to reuse connection.

"""
__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "peisach@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import sys
from wwpdb.utils.db.MyConnectionBase import MyConnectionBase

import logging
logger = logging.getLogger(__name__)


class DaInternal(MyConnectionBase):
    __schemaMap = { "PDBID_TO_DEPID" : "select Structure_ID from rcsb_status where pdb_id = '%s'",
                    "DEPID_TO_PDBID" : "select pdb_id from rcsb_status where Structure_id = '%s'",
                    "PDBID_TO_ASSOC_EMDBID": """select a.db_id from pdbx_database_related a, rcsb_status b
                                    where a.structure_id = b.structure_id
                                    and a.db_name = 'EMDB' and a.content_type = 'associated EM volume'
                                    and b.pdb_id = '%s'"""
    }

    def __init__(self, siteId=None, verbose=True, log=sys.stderr):
        super(DaInternal, self).__init__(siteId=siteId, verbose=verbose, log=log)
        self.__verbose = verbose
        self.__siteId = siteId
        self.__lfh = log
        self.setResource('DA_INTERNAL')

    def __del__(self):
        if self.getConnection():
            logger.debug("Del closing DB")
            self.closeConnection()

    def __openconnection(self):
        if not self.getConnection():
            logger.debug("Opening db")
            try:
                self.openConnection()
            except:
                logger.exception("Failing opening DB connection to da_internal")

    def selectData(self, key=None, parameter=()):
        """
        """
        if not key or not self.__schemaMap or (not key in self.__schemaMap):
            return None
        #
        sql = self.__schemaMap[key]
        if parameter:
            sql = self.__schemaMap[key] % parameter
        #
        return self.runSelectSQL(sql)

    def runSelectSQL(self, query):
        rows = ()
        try:
            self.__openconnection()
            curs = self.getCursor()
            curs.execute(query)
            rows = curs.fetchall()
            curs.close()
        except:
            logger.exception("Unable to request")

        return rows
    

    def get_depid_from_pdb(self, pdbid):
        ret = self.selectData(key='PDBID_TO_DEPID', parameter=(pdbid))
        if ret:
            # Single DepID
            return ret[0][0]
        else:
            return None

    def get_pdbid_from_depid(self, depid):
        ret = self.selectData(key='DEPID_TO_PDBID', parameter=(depid))
        if ret:
            return ret[0][0]
        else:
            return None

