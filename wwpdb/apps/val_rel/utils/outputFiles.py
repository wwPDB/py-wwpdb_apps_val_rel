import logging
import os

from wwpdb.utils.config.ConfigInfo import getSiteId

from wwpdb.io.locator.ReleaseFileNames import ReleaseFileNames
from wwpdb.io.locator.ReleasePathInfo import ReleasePathInfo

logger = logging.getLogger(__name__)


class outputFiles:
    def __init__(
            self,
            pdbID=None,
            emdbID=None,
            outputRoot="",
            siteID=getSiteId(),
            skip_pdb_hash=False,
            validation_sub_directory="current",
    ):
        self._pdbID = pdbID
        self._emdbID = emdbID
        self._siteID = siteID
        self._output_root = outputRoot
        self._validation_sub_directory = validation_sub_directory
        self._entryID = None
        self.skip_pdb_hash = skip_pdb_hash
        self.entry_output_folder = self.get_entry_output_folder()
        self.with_emdb = False
        self.copy_to_root_emdb = False
        self.accession = ""
        self.rf = ReleaseFileNames()
        self.rp = ReleasePathInfo(self._siteID)

    def get_pdb_root_folder(self):
        rp = ReleasePathInfo(self._siteID)
        return os.path.join(
            rp.getForReleasePath("val_reports"), self._validation_sub_directory
        )

    def get_root_state_folder(self):
        # Place under pdb val-reports as extra director
        rp = ReleasePathInfo(self._siteID)
        return os.path.join(
            rp.getForReleasePath("val_reports"),
            self._validation_sub_directory + "_state",
        )

    def get_emdb_root_folder(self):
        rp = ReleasePathInfo(self._siteID)
        return os.path.join(
            rp.getForReleasePath("em_val_reports"),
            self._validation_sub_directory
        )

    def set_validation_subdirectory(self, sub_dir):
        self._validation_sub_directory = sub_dir

    def set_entry_id(self, entry_id):
        self._entryID = entry_id

    def set_pdb_id(self, entry_id):
        self._pdbID = entry_id

    def set_emdb_id(self, entry_id):
        self._emdbID = entry_id

    def get_pdb_id(self):
        if self._pdbID:
            return self._pdbID
        return ""

    def get_pdb_id_hash(self):
        if self.get_pdb_id():
            return self.get_pdb_id()[1:3]
        return ""

    def get_emdb_id(self):
        if self._emdbID:
            return self._emdbID
        return ""

    def get_emdb_lower_hyphen(self):
        if self.get_emdb_id():
            return self.rf.get_lower_emdb_hyphen_format(self.get_emdb_id())
        return ""

    def get_emdb_lower_underscore(self):
        if self.get_emdb_id():
            return self.rf.get_lower_emdb_underscore_format(self.get_emdb_id())
        return ""

    def get_entry_id(self):
        if self._entryID:
            return self._entryID
        return ""

    def set_accession_variables(self, with_emdb=False, copy_to_root_emdb=False):
        self.with_emdb = with_emdb
        self.copy_to_root_emdb = copy_to_root_emdb

    def set_accession(self):
        self.accession = "{}".format(self._entryID)
        if self._emdbID and not self._pdbID:
            self.accession = self.get_emdb_lower_underscore()
        if self._pdbID and self._emdbID and self.with_emdb:
            self.accession = "{}_{}".format(self.get_emdb_lower_underscore(), self._pdbID)
        if self._emdbID and self.copy_to_root_emdb:
            self.accession = "{}".format(self.get_emdb_lower_underscore())

        return self.accession

    def add_output_folder_accession(self, filename):
        return filename
        # return os.path.join(self.entry_output_folder, filename)

    def get_validation_xml(self):
        return self.add_output_folder_accession(
            self.rf.get_validation_xml(self.accession)
        )

    def get_validation_png(self):
        return self.add_output_folder_accession(
            self.rf.get_validation_png(self.accession)
        )

    def get_validation_svg(self):
        return self.add_output_folder_accession(
            self.rf.get_validation_svg(self.accession)
        )

    def get_validation_pdf(self):
        return self.add_output_folder_accession(
            self.rf.get_validation_pdf(self.accession)
        )

    def get_validation_full_pdf(self):
        return self.add_output_folder_accession(
            self.rf.get_validation_full_pdf(self.accession)
        )

    def get_validation_2fofc(self):
        return self.add_output_folder_accession(
            self.rf.get_validation_2fofc(self.accession)
        )

    def get_validation_fofc(self):
        return self.add_output_folder_accession(
            self.rf.get_validation_fofc(self.accession)
        )

    def get_core_validation_files(self):
        logger.debug("getting core files for: %s", self._entryID)
        logger.debug("path: %s", self.entry_output_folder)

        self.set_accession()
        logger.debug("accession set to %s", self.accession)

        ret = {}
        ret["pdf"] = self.get_validation_pdf()
        ret["full_pdf"] = self.get_validation_full_pdf()
        ret["xml"] = self.get_validation_xml()
        ret["png"] = self.get_validation_png()
        ret["svg"] = self.get_validation_svg()

        logger.debug(ret)

        return ret

    def get_extra_validation_files(self):

        ret = {}
        ret["2fofc"] = self.get_validation_2fofc()
        ret["fofc"] = self.get_validation_fofc()

        return ret

    def get_all_validation_files(self):
        core_file_dict = self.get_core_validation_files()
        extra_file_dict = self.get_extra_validation_files()

        all_file_dict = core_file_dict.copy()
        all_file_dict.update(extra_file_dict)

        return all_file_dict

    def get_pdb_output_folder(self):
        self.set_entry_id(self.get_pdb_id())
        if self.skip_pdb_hash:
            pdb_hash = ""
        else:
            pdb_hash = self.get_pdb_id_hash()
        if self._output_root:
            self.entry_output_folder = os.path.join(
                self._output_root, pdb_hash, self.get_pdb_id()
            )
        else:
            self.entry_output_folder = os.path.join(
                self.get_pdb_root_folder(), self.get_pdb_id()
            )
        return self.entry_output_folder

    def get_emdb_output_folder(self):
        self.set_entry_id(self.get_emdb_id())
        if self._output_root:
            self.entry_output_folder = os.path.join(
                self._output_root, self.get_emdb_id()
            )
        else:
            self.entry_output_folder = os.path.join(
                self.get_emdb_root_folder(), self.get_emdb_id(), "validation"
            )
        return self.entry_output_folder

    def get_entry_output_folder(self):

        if self.get_pdb_id():
            return self.get_pdb_output_folder()
        elif self.get_emdb_id():
            return self.get_emdb_output_folder()
        return ""
