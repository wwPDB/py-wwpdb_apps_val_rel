import glob
import os
from wwpdb.io.locator.ReleasePathInfo import ReleasePathInfo
from wwpdb.utils.config.ConfigInfo import ConfigInfo, getSiteId

class FindEntries:
    def __init__(self, siteID=getSiteId()):
        self.siteID = siteID
        self.cI = ConfigInfo(self.siteID)
        self.entries_missing_files = []
        self.missing_files = []

    def _get_release_entries(self, subfolder):
        """Returns list of entries in for_release/subfolder directory.
        Ignores directories that end in ".new" being created by release module.
        """
        entries = list()
        rpi = ReleasePathInfo(self.siteID)
        dirpath = rpi.getForReleasePath(subdir=subfolder)
        full_entries = glob.glob(os.path.join(dirpath, "*"))
        for full_entry in full_entries:
            if ".new" not in full_entry:
                # Ensure not some other random file
                if os.path.isdir(full_entry):
                    entry = os.path.basename(full_entry)
                    entries.append(entry)
        return entries

    def get_modified_pdb_entries(self):
        """Returns list of entries in the for_release/modified directory"""
        return self._get_release_entries(subfolder="modified")

    def get_added_pdb_entries(self):
        """Return list of entries in the for_release/added directory"""
        return self._get_release_entries(subfolder="added")

    def get_emdb_entries(self):
        """Return list of entries in the for_release/emd directory"""
        return self._get_release_entries(subfolder="emd")
