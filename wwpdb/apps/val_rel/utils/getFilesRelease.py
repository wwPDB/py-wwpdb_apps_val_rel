import os
import logging
from wwpdb.utils.config.ConfigInfo import ConfigInfo, getSiteId
from wwpdb.io.locator.ReleasePathInfo import ReleasePathInfo
from wwpdb.io.locator.ReleaseFileNames import ReleaseFileNames

logger = logging.getLogger(__name__)


class getFilesRelease:
    """Class to access prior/public release files"""
    def __init__(self, siteID=getSiteId()):
        self.__siteID = siteID
        self.__cI = ConfigInfo(self.__siteID)
        self.__rp = ReleasePathInfo(self.__siteID)
        self.__rf = ReleaseFileNames()

        self.__local_ftp_mmcif_path = self.__cI.get("SITE_MMCIF_DIR", "")
        self.__local_ftp_sf_path = self.__cI.get("SITE_STRFACTORS_DIR", "")
        self.__local_ftp_cs_path = self.__cI.get("CHEMICAL_SHIFTS_FTP", "")
        self.__local_ftp_emdb_path = self.__cI.get("SITE_EMDB_FTP", "")

    def _get_pdb_path_search_order(self, pdbid, coordinates=False, sf=False, cs=False):
        ret_list = [
            os.path.join(self.__rp.getForReleasePath("added"), pdbid),
            os.path.join(self.__rp.getForReleasePath("modified"), pdbid),
            os.path.join(self.__rp.getForReleasePath("added", version="previous"), pdbid),
            os.path.join(
                self.__rp.getForReleasePath("modified", version="previous"), pdbid
            ),
        ]
        if coordinates:
            ret_list.append(self.__local_ftp_mmcif_path)
        if sf:
            ret_list.append(self.__local_ftp_sf_path)
        if cs:
            ret_list.append(self.__local_ftp_cs_path)
        return ret_list

    def _search_nfs_pdb(self, filename, pdbid, coordinates=False, sf=False, cs=False):
        for path in self._get_pdb_path_search_order(
            pdbid, coordinates=coordinates, sf=sf, cs=cs
        ):
            file_path = os.path.join(path, filename)
            logger.debug("searching: {}".format(file_path))
            if os.path.exists(file_path):
                logging.debug("found: {}".format(file_path))
                return file_path
        return None

    def get_model(self, pdbid):
        file_path = self._search_nfs_pdb(
            filename=self.__rf.get_model(pdbid), pdbid=pdbid, coordinates=True
        )
        if file_path:
            return file_path
        return None

    def get_sf(self, pdbid):
        file_path = self._search_nfs_pdb(
            filename=self.__rf.get_structure_factor(pdbid, for_release=True),
            pdbid=pdbid,
            sf=True,
        )
        if file_path:
            return file_path
        file_path = self._search_nfs_pdb(
            filename=self.__rf.get_structure_factor(pdbid), pdbid=pdbid, sf=True
        )
        if file_path:
            return file_path
        return None

    def get_cs(self, pdbid):
        file_path = self._search_nfs_pdb(
            filename=self.__rf.get_chemical_shifts(pdbid, for_release=True),
            pdbid=pdbid,
            cs=True,
        )
        if file_path:
            return file_path
        file_path = self._search_nfs_pdb(
            filename=self.__rf.get_chemical_shifts(pdbid), pdbid=pdbid, cs=True
        )
        if file_path:
            return file_path
        return None

    def get_emdb_path_search_order(self, emdbid, subfolder):
        ret_list = [
                self.__rp.getForReleasePath(subdir="emd", accession=emdbid, em_sub_path=subfolder),
                self.__rp.getForReleasePath(
                    subdir="emd", version="previous", accession=emdbid, em_sub_path=subfolder),
            os.path.join(self.__local_ftp_emdb_path, emdbid, subfolder),
        ]

        return ret_list

    def return_emdb_path(self, filename, subfolder, emdbid):
        for path in self.get_emdb_path_search_order(emdbid=emdbid, subfolder=subfolder):
            file_path = os.path.join(path, filename)
            logging.debug(file_path)
            if os.path.exists(file_path):
                return file_path
        return None

    def get_emdb_xml(self, emdbid):
        filepath = self.return_emdb_path(
            filename=self.__rf.get_emdb_xml(emdbid, for_release=True),
            subfolder="header",
            emdbid=emdbid,
        )
        if filepath:
            return filepath
        filepath = self.return_emdb_path(
            filename=self.__rf.get_emdb_xml(emdbid), subfolder="header", emdbid=emdbid
        )
        if filepath:
            return filepath
        return None

    def get_emdb_volume(self, emdbid):
        return self.return_emdb_path(
            filename=self.__rf.get_emdb_map(emdbid), subfolder="map", emdbid=emdbid
        )

    def get_emdb_fsc(self, emdbid):
        return self.return_emdb_path(
            filename=self.__rf.get_emdb_fsc(emdbid), subfolder="fsc", emdbid=emdbid
        )
