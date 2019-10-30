import logging
import os
from wwpdb.apps.val_rel.release_file_names import releaseFileNames
from wwpdb.utils.config.ConfigInfo import ConfigInfo, getSiteId

class outputFiles:
    def __init__(self, pdbID=None, emdbID=None, outputRoot='', siteID=getSiteId(), skip_pdb_hash=False):
        self._pdbID = pdbID
        self._emdbID = emdbID
        self.output_root = outputRoot
        self._entryID = None
        self.skip_pdb_hash = skip_pdb_hash
        self.entry_output_folder = self.get_entry_output_folder()
        self.with_emdb = False
        self.copy_to_root_emdb = False
        self.accession = ''
        self.rf = releaseFileNames(gzip=False)
        self.cI = ConfigInfo(siteID)

    def set_entry_id(self, entry_id):
        self._entryID = entry_id

    def set_pdb_id(self, entry_id):
        self._pdbID = entry_id

    def set_emdb_id(self, entry_id):
        self._emdbID = entry_id

    def get_pdb_id(self):
        if self._pdbID:
            return self._pdbID
        return ''

    def get_pdb_id_hash(self):
        if self.get_pdb_id():
            return self.get_pdb_id()[1:3]
        return ''

    def get_emdb_id(self):
        if self._emdbID:
            return self._emdbID
        return ''

    def get_emdb_lower_underscore(self):
        if self.get_emdb_id():
            return self.get_emdb_id().lower().replace("-", "_")
        return ''

    def get_entry_id(self):
        if self._entryID:
            return self._entryID
        return ''

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
        return os.path.join(self.entry_output_folder, filename)

    def get_core_validation_files(self):
        logging.debug("getting core files for: {}".format(self._entryID))
        logging.debug(
            "path: {}".format(os.path.join(self.entry_output_folder, self._entryID))
        )

        self.set_accession()
        logging.debug('accession set to {}'.format(self.accession))

        ret = {}
        ret["pdf"] = self.add_output_folder_accession(self.rf.get_validation_pdf(self.accession))
        ret["full_pdf"] = self.add_output_folder_accession(self.rf.get_validation_full_pdf(self.accession))
        ret["xml"] = self.add_output_folder_accession(self.rf.get_validation_xml(self.accession))
        ret["png"] = self.add_output_folder_accession(self.rf.get_validation_png(self.accession))
        ret["svg"] = self.add_output_folder_accession(self.rf.get_validation_svg(self.accession))

        return ret

    def get_extra_validation_files(self):
        
        ret = {}
        ret["2fofc"] = self.add_output_folder_accession(self.rf.get_2fofc(self.accession))
        ret["fofc"] = self.add_output_folder_accession(self.rf.get_fofc(self.accession))

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
            pdb_hash = ''
        else:
            pdb_hash = self.get_pdb_id_hash()
        if self.output_root:
            self.entry_output_folder = os.path.join(self.output_root, pdb_hash,  self.get_pdb_id())
        else:
            self.entry_output_folder = os.path.join(
                self.cI.get("VALIDATION_EXCHANGE_DATA_PATH"), self.get_pdb_id()
            )
        return self.entry_output_folder

    def get_emdb_output_folder(self):
        self.set_entry_id(self.get_emdb_id())
        if self.output_root:
            self.entry_output_folder = os.path.join(self.output_root, self.get_emdb_id())
        else:
            self.entry_output_folder = os.path.join(
                self.cI.get("VALIDATION_EXCHANGE_DATA_PATH"),
                "emd",
                self.get_emdb_id(),
                "validation",
            )
        return self.entry_output_folder

    def get_entry_output_folder(self):

        if self.get_pdb_id():
            return self.get_pdb_output_folder()
        elif self.get_emdb_id():
            return self.get_emdb_output_folder()
        return ''
