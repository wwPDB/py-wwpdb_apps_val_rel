import logging
import os
from typing import List, Literal, Optional, Tuple

from wwpdb.io.locator.ReleaseFileNames import ReleaseFileNames
from wwpdb.io.locator.ReleasePathInfo import ReleasePathInfo
from wwpdb.utils.config.ConfigInfo import getSiteId

from wwpdb.apps.val_rel.utils.getFilesReleaseBase import raise_no_emdb, raise_no_pdb

logger = logging.getLogger(__name__)


class getFilesReleaseOneDep:
    """Class to access prior/public release files"""

    def __init__(self, pdb_id: Optional[str], emdb_id: Optional[str], siteID: Optional[str] = None) -> None:
        if siteID is None:
            siteID = getSiteId()
        self.__siteID = siteID
        self.__pdb_id = pdb_id
        self.__emdb_id = emdb_id
        self.__rp = ReleasePathInfo(self.__siteID)
        self.__rf = ReleaseFileNames()

    def _get_onedep_pdb_folder_paths(self) -> List[str]:
        ret_list = [
            self.__rp.get_added_path(),
            self.__rp.get_modified_path(),
        ]
        return ret_list

    def _get_previous_onedep_pdb_folder_paths(self) -> List[str]:
        ret_list = [self.__rp.get_previous_added_path(), self.__rp.get_previous_modified_path()]
        return ret_list

    def _get_onedep_pdb_file_paths(self, filename: str) -> List[str]:
        """Returns list of directories for self.__pdb_id and filename.
        Returns for_release/{added, modified}/pdb_id/filename
        """
        ret_list = []
        folder_list = self._get_onedep_pdb_folder_paths()
        if not self.__pdb_id:
            emsg = "PDB ID is not set. Cannot get OneDep PDB file paths."
            raise ValueError(emsg)
        for folder in folder_list:
            full_file_name = os.path.join(folder, self.__pdb_id, filename)
            ret_list.append(full_file_name)
        return ret_list

    def _get_onedep_previous_pdb_file_paths(self, filename: str) -> List[str]:
        """Returns list of directories for self.__pdb_id and filename.
        Returns for_release/previous/{added, modified}/pdb_id/filename
        """
        ret_list = []
        folder_list = self._get_previous_onedep_pdb_folder_paths()
        if not self.__pdb_id:
            emsg = "PDB ID is not set. Cannot get OneDep previous PDB file paths."
            raise ValueError(emsg)
        for folder in folder_list:
            full_file_name = os.path.join(folder, self.__pdb_id, filename)
            ret_list.append(full_file_name)
        return ret_list

    def _check_onedep_pdb_file_paths(self, filename: str) -> Optional[str]:
        """Checks for_release/{added,modified}/pdb_id/filename in order and returns
        whichever exists or None"""
        for onedep_file in self._get_onedep_pdb_file_paths(filename=filename):
            logger.debug("searching: %s", onedep_file)
            if os.path.exists(onedep_file):
                logger.debug("found: %s", onedep_file)
                return onedep_file
        return None

    def _check_onedep_previous_pdb_file_paths(self, filename: str) -> Optional[str]:
        """Checks for_release/previous/{added,modified}/pdb_id/filename in order and returns
        whichever exists or None"""
        for onedep_file in self._get_onedep_previous_pdb_file_paths(filename=filename):
            logger.debug("searching: %s", onedep_file)
            if os.path.exists(onedep_file):
                logger.debug("found: %s", onedep_file)
                return onedep_file
        return None

    def check_pdb_current_then_previous(self, filename: str) -> Tuple[Optional[str], bool]:
        """Locates filename in for_release/{added,modified}/pdb_id/filename
        and if not found for_release/previous/{added,modified}/pdb_id/filename

        Returns (file_path, cur_week) where file_path is the path or None
        and cur_week is a boolean indicating if it is current_week release.
        """
        file_path = self._check_onedep_pdb_file_paths(filename=filename)
        if file_path:
            return file_path, True
        file_path = self._check_onedep_previous_pdb_file_paths(filename=filename)
        if file_path:
            return file_path, False
        return None, False

    def check_emdb_current_then_previous(
        self,
        filename: str,
        subfolder: Literal["header", "map", "fsc", "images", "masks", "metadata", "other", "validation"],
    ) -> Tuple[Optional[str], bool]:
        """Looks for filename in for_release/emd/emdb_id/subfolder/filename
        and if not found for_release/previous/....

        Returns (file_path, cur_week) where file_path is the path or None
        and cur_week is a boolean indicating if it is current_week release.
        """
        if self.__emdb_id is None:
            raise_no_emdb()
        for_release_current_path = self.__rp.get_emd_subfolder_path(accession=self.__emdb_id, subfolder=subfolder)
        file_path = os.path.join(for_release_current_path, filename)
        if os.path.exists(file_path):
            return file_path, True
        for_release_previous_path = self.__rp.get_previous_emd_subfolder_path(
            accession=self.__emdb_id, subfolder=subfolder
        )
        file_path = os.path.join(for_release_previous_path, filename)
        if os.path.exists(file_path):
            return file_path, False
        return None, False

    def get_model(self) -> Tuple[Optional[str], bool]:
        if self.__pdb_id is None:
            raise_no_pdb()
        filename = self.__rf.get_model(self.__pdb_id, for_release=True)
        return self.check_pdb_current_then_previous(filename=filename)

    def get_sf(self) -> Tuple[Optional[str], bool]:
        if self.__pdb_id is None:
            raise_no_pdb()
        filename = self.__rf.get_structure_factor(self.__pdb_id, for_release=True)
        return self.check_pdb_current_then_previous(filename=filename)

    def get_cs(self) -> Tuple[Optional[str], bool]:
        if self.__pdb_id is None:
            raise_no_pdb()
        filename = self.__rf.get_chemical_shifts(self.__pdb_id, for_release=True)
        return self.check_pdb_current_then_previous(filename=filename)

    def get_nmr_data(self) -> Tuple[Optional[str], bool]:
        if self.__pdb_id is None:
            raise_no_pdb()
        filename = self.__rf.get_nmr_data(self.__pdb_id, for_release=True)
        return self.check_pdb_current_then_previous(filename=filename)

    def get_emdb_xml(self) -> Tuple[Optional[str], bool]:
        if self.__emdb_id is None:
            raise_no_emdb()
        return self.check_emdb_current_then_previous(
            filename=self.__rf.get_emdb_xml(self.__emdb_id, for_release=True),
            subfolder="header",
        )

    def get_emdb_volume(self) -> Tuple[Optional[str], bool]:
        if self.__emdb_id is None:
            raise_no_emdb()
        return self.check_emdb_current_then_previous(filename=self.__rf.get_emdb_map(self.__emdb_id), subfolder="map")

    def get_emdb_fsc(self) -> Tuple[Optional[str], bool]:
        if self.__emdb_id is None:
            raise_no_emdb()
        return self.check_emdb_current_then_previous(filename=self.__rf.get_emdb_fsc(self.__emdb_id), subfolder="fsc")

    def get_emdb_metadata(self) -> Tuple[Optional[str], bool]:
        if self.__emdb_id is None:
            raise_no_emdb()

        return self.check_emdb_current_then_previous(
            filename=self.__rf.get_emdb_metadata(self.__emdb_id), subfolder="metadata"
        )
