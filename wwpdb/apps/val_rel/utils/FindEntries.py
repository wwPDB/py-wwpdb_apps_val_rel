import glob
import os
from typing import List, Literal, Optional, Tuple

from wwpdb.io.locator.ReleasePathInfo import ReleasePathInfo
from wwpdb.utils.config.ConfigInfo import getSiteId


class FindEntries:
    def __init__(self, siteID: Optional[str] = None) -> None:
        if siteID is None:
            siteID = getSiteId()
        self.__siteID = siteID
        # self.entries_missing_files = []
        # self.missing_files = []

    def __get_rel_files(self, subfolder: Literal["added", "modified", "emd"]) -> Tuple[List[str], List[str]]:
        """Internal function to returns list of entries and paths in for_release/subfolder directory.
        Ignores directories that end in ".new" being created by release module.
        """
        entries: List[str] = []
        ent_paths: List[str] = []
        rpi = ReleasePathInfo(self.__siteID)
        dirpath = rpi.getForReleasePath(subdir=subfolder)
        full_entries = glob.glob(os.path.join(dirpath, "*"))
        for full_entry in full_entries:
            if ".new" not in full_entry:
                # Ensure not some other random file
                if os.path.isdir(full_entry):
                    entry = os.path.basename(full_entry)
                    entries.append(entry)
                    ent_paths.append(full_entry)
        return entries, ent_paths

    def _get_release_entries(self, subfolder: Literal["added", "modified", "emd"]) -> List[str]:
        """Returns list of entries in for_release/subfolder directory.
        Ignores directories that end in ".new" being created by release module.
        """
        entries, _entpaths = self.__get_rel_files(subfolder)
        return entries

    def get_modified_pdb_entries(self) -> List[str]:
        """Returns list of entries in the for_release/modified directory"""
        return self._get_release_entries(subfolder="modified")

    def get_added_pdb_entries(self) -> List[str]:
        """Return list of entries in the for_release/added directory"""
        return self._get_release_entries(subfolder="added")

    def get_emdb_entries(self) -> List[str]:
        """Return list of entries in the for_release/emd directory"""
        return self._get_release_entries(subfolder="emd")

    def _get_release_paths(self, subfolder: Literal["added", "modified", "emd"]) -> List[str]:
        """Returns list of paths in for_release/subfolder directory.
        Ignores directories that end in ".new" being created by release module.
        """
        _entries, entpaths = self.__get_rel_files(subfolder)
        return entpaths

    def get_modified_pdb_paths(self) -> List[str]:
        """Returns list of paths in the for_release/modified directory"""
        return self._get_release_paths(subfolder="modified")

    def get_added_pdb_paths(self) -> List[str]:
        """Return list of paths in the for_release/added directory"""
        return self._get_release_paths(subfolder="added")

    def get_emdb_paths(self) -> List[str]:
        """Return list of paths in the for_release/emd directory"""
        return self._get_release_paths(subfolder="emd")
