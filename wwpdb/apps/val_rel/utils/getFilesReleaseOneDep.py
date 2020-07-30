import logging
import os

from wwpdb.io.locator.ReleaseFileNames import ReleaseFileNames
from wwpdb.io.locator.ReleasePathInfo import ReleasePathInfo
from wwpdb.utils.config.ConfigInfo import ConfigInfo, getSiteId

logger = logging.getLogger(__name__)


class getFilesReleaseOneDep:
    """Class to access prior/public release files"""

    def __init__(self, pdb_id, emdb_id, siteID=getSiteId()):
        self.__siteID = siteID
        self.pdb_id = pdb_id
        self.emdb_id = emdb_id
        self.__cI = ConfigInfo(self.__siteID)
        self.__rp = ReleasePathInfo(self.__siteID)
        self.__rf = ReleaseFileNames()
        self.sf_current = False
        self.cs_current = False
        self.mr_current = False
        self.em_xml_current = False

    def _get_onedep_pdb_folder_paths(self):
        ret_list = [
            self.__rp.get_added_path(),
            self.__rp.get_modified_path(),
        ]
        return ret_list

    def _get_previous_onedep_pdb_folder_paths(self):
        ret_list = [
            self.__rp.get_previous_added_path(),
            self.__rp.get_previous_modified_path()
        ]
        return ret_list

    def _get_onedep_pdb_file_paths(self, filename):
        ret_list = []
        folder_list = self._get_onedep_pdb_folder_paths()
        for folder in folder_list:
            full_file_name = os.path.join(folder, self.pdb_id, filename)
            ret_list.append(full_file_name)
        return ret_list

    def _get_onedep_previous_pdb_file_paths(self, filename):
        ret_list = []
        folder_list = self._get_previous_onedep_pdb_folder_paths()
        for folder in folder_list:
            full_file_name = os.path.join(folder, self.pdb_id, filename)
            ret_list.append(full_file_name)
        return ret_list

    def _check_onedep_pdb_file_paths(self, filename):
        for onedep_file in self._get_onedep_pdb_file_paths(filename=filename):
            logger.debug("searching: %s", onedep_file)
            if os.path.exists(onedep_file):
                logger.debug("found: %s", onedep_file)
                return onedep_file
        return None

    def _check_onedep_previous_pdb_file_paths(self, filename):
        for onedep_file in self._get_onedep_previous_pdb_file_paths(filename=filename):
            logger.debug("searching: %s", onedep_file)
            if os.path.exists(onedep_file):
                logger.debug("found: %s", onedep_file)
                return onedep_file
        return None

    def check_pdb_current_then_previous(self, filename):
        file_path = self._check_onedep_pdb_file_paths(filename=filename)
        if file_path:
            return file_path, True
        file_path = self._check_onedep_previous_pdb_file_paths(filename=filename)
        if file_path:
            return file_path, False
        return None, False

    def check_emdb_current_then_previous(self, filename, subfolder):
        for_release_current_path = self.__rp.get_emd_subfolder_path(accession=self.emdb_id, subfolder=subfolder)
        file_path = os.path.join(for_release_current_path, filename)
        if os.path.exists(file_path):
            return file_path, True
        for_release_previous_path = self.__rp.get_previous_emd_subfolder_path(accession=self.emdb_id, subfolder=subfolder)
        file_path = os.path.join(for_release_previous_path, filename)
        if os.path.exists(file_path):
            return file_path, False
        return None, False

    def get_model(self):
        filename = self.__rf.get_model(self.pdb_id, for_release=True)
        return self.check_pdb_current_then_previous(filename=filename)

    def get_sf(self):
        filename = self.__rf.get_structure_factor(self.pdb_id, for_release=True)
        return self.check_pdb_current_then_previous(filename=filename)

    def get_cs(self):
        filename = self.__rf.get_chemical_shifts(self.pdb_id, for_release=True)
        return self.check_pdb_current_then_previous(filename=filename)

    def get_nmr_data(self):
        filename = self.__rf.get_nmr_data(self.pdb_id, for_release=True)
        return self.check_pdb_current_then_previous(filename=filename)

    def get_emdb_xml(self):
        return self.check_emdb_current_then_previous(
            filename=self.__rf.get_emdb_xml(self.emdb_id, for_release=True),
            subfolder="header",
        )

    def get_emdb_volume(self):
        return self.check_emdb_current_then_previous(
            filename=self.__rf.get_emdb_map(self.emdb_id), subfolder="map")

    def get_emdb_fsc(self):
        return self.check_emdb_current_then_previous(
            filename=self.__rf.get_emdb_fsc(self.emdb_id), subfolder="fsc")
