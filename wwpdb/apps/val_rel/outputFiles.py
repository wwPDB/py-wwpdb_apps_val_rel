import logging
import os

class outputFiles:
    def __init__(self, pdbID=None, emdbID=None, outputRoot='', skip_pdb_hash=False):
        self._pdbID = pdbID
        self._emdbID = emdbID
        self.output_root = outputRoot
        self._entryID = None
        self.skip_pdb_hash = skip_pdb_hash
        self.entry_output_folder = self.get_entry_output_folder()
        self.with_emdb = False
        self.copy_to_root_emdb = False
        self.accession = ''

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
        self.accession = "{}".format(self.get_entry_id())
        if self.get_emdb_id() and not self.get_pdb_id():
            self.accession = self.get_emdb_lower_underscore()
        if self.get_pdb_id() and self.get_emdb_id() and self.with_emdb:
            self.accession = "{}_{}".format(self.get_emdb_lower_underscore(), self.get_pdb_id())
        if self.get_emdb_id() and self.copy_to_root_emdb:
            self.accession = "{}".format(self.get_emdb_lower_underscore())
        
        return self.accession

    def get_validation_pdf(self):
        return self.accession + "_validation.pdf"
    
    def get_validation_full_pdf(self):
        return self.accession + "_full_validation.pdf"

    def get_validation_xml(self):
        return self.accession + "_validation.xml"

    def get_validation_png(self):
        return self.accession + "_multipercentile_validation.png"

    def get_validation_svg(self):
        return self.accession + "_multipercentile_validation.svg"

    def get_2fofc(self):
        return self.accession + "_validation_2fo-fc_map_coef.cif"

    def get_fofc(self):
        return self.accession + "_validation_fo-fc_map_coef.cif"

    def add_output_folder_accession(self, filename):
        return os.path.join(self.get_entry_output_folder(), filename)

    def get_core_validation_files(self):
        logging.debug("getting core files for: {}".format(self.get_entry_id()))
        logging.debug(
            "path: {}".format(os.path.join(self.get_entry_output_folder(), self.get_entry_id()))
        )

        self.set_accession()
        logging.debug('accession set to {}'.format(self.accession))

        ret = {}
        ret["pdf"] = self.add_output_folder_accession(self.get_validation_pdf())
        ret["full_pdf"] = self.add_output_folder_accession(self.get_validation_full_pdf())
        ret["xml"] = self.add_output_folder_accession(self.get_validation_xml())
        ret["png"] = self.add_output_folder_accession(self.get_validation_png())
        ret["svg"] = self.add_output_folder_accession(self.get_validation_svg())

        return ret

    def get_extra_validation_files(self):
        
        ret = {}
        ret["2fofc"] = self.add_output_folder_accession(self.get_2fofc())
        ret["fofc"] = self.add_output_folder_accession(self.get_fofc())

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
        self.entry_output_folder = os.path.join(self.output_root, pdb_hash, self.get_pdb_id())
        return self.entry_output_folder

    def get_emdb_output_folder(self):
        self.set_entry_id(self.get_emdb_id())
        self.entry_output_folder = os.path.join(self.output_root, 'emd', self.get_emdb_id(), 'validation')
        return self.entry_output_folder

    def get_entry_output_folder(self):

        if self.get_pdb_id():
            return self.get_pdb_output_folder()
        elif self.get_emdb_id():
            return self.get_emdb_output_folder()
        return ''
