import os
import logging
from wwpdb.utils.config.ConfigInfo import ConfigInfo, getSiteId
from wwpdb.io.locator.ReleasePathInfo import ReleasePathInfo
from wwpdb.io.locator.ReleaseFileNames import ReleaseFileNames
from wwpdb.io.locator.localFTPPathInfo import LocalFTPPathInfo

logger = logging.getLogger(__name__)


class getFilesRelease:
    """Class to access prior/public release files"""
    def __init__(self, siteID=getSiteId()):
        self.__siteID = siteID
        self.__cI = ConfigInfo(self.__siteID)
        self.__rp = ReleasePathInfo(self.__siteID)
        self.__rf = ReleaseFileNames()
        self.__lf = LocalFTPPathInfo()
        self.__local_ftp_emdb_path = self.__lf.get_ftp_emdb()

    def _get_onedep_pdb_folder_paths(self):
        ret_list = [
            self.__rp.get_added_path(),
            self.__rp.get_modified_path(),
            self.__rp.get_previous_added_path(),
            self.__rp.get_previous_modified_path()
        ]
        return ret_list

    def _get_onedep_pdb_file_paths(self, pdbid, filename):
        ret_list = []
        folder_list = self._get_onedep_pdb_folder_paths()
        for folder in folder_list:
            full_file_name = os.path.join(folder, pdbid, filename)
            ret_list.append(full_file_name)
        return ret_list

    def _check_onedep_pdb_file_paths(self, pdbid, filename):
        for onedep_file in self._get_onedep_pdb_file_paths(pdbid=pdbid, filename=filename):
            logger.debug("searching: %s", onedep_file)
            if os.path.exists(onedep_file):
                logging.debug("found: %s", onedep_file)
                return onedep_file
        return None

    def get_model(self, pdbid):
        filename = self.__rf.get_model(pdbid, for_release=True)
        file_path = self._check_onedep_pdb_file_paths(pdbid=pdbid, filename=filename)
        if file_path:
            return file_path
        local_ftp_file_name = self.__lf.get_model_fname(accession=pdbid)
        if os.path.exists(local_ftp_file_name):
            return local_ftp_file_name
        return None

    def get_sf(self, pdbid):
        filename = self.__rf.get_structure_factor(pdbid, for_release=True)
        file_path = self._check_onedep_pdb_file_paths(pdbid=pdbid, filename=filename)
        if file_path:
            return file_path
        local_ftp_file_name = self.__lf.get_structure_factors_fname(accession=pdbid)
        if os.path.exists(local_ftp_file_name):
            return local_ftp_file_name
        return None

    def get_cs(self, pdbid):
        filename = self.__rf.get_chemical_shifts(pdbid, for_release=True)
        file_path = self._check_onedep_pdb_file_paths(pdbid=pdbid, filename=filename)
        if file_path:
            return file_path
        local_ftp_file_name = self.__lf.get_chemical_shifts_fname(accession=pdbid)
        if os.path.exists(local_ftp_file_name):
            return local_ftp_file_name
        return None

    def get_nmr_data(self, pdbid):
        filename = self.__rf.get_nmr_data(pdbid, for_release=True)
        file_path = self._check_onedep_pdb_file_paths(pdbid=pdbid, filename=filename)
        if file_path:
            return file_path
        local_ftp_file_name = self.__lf.get_nmr_data_fname(accession=pdbid)
        if os.path.exists(local_ftp_file_name):
            return local_ftp_file_name
        return None

    def get_emdb_path_search_order(self, emdbid, subfolder):
        ret_list = [
            self.__rp.get_emd_subfolder_path(accession=emdbid, em_sub_path=subfolder),
            self.__rp.get_previous_emd_subfolder_path(accession=emdbid, em_sub_path=subfolder),
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
