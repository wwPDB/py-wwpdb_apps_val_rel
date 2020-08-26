import argparse
import logging
import os
from pprint import pprint

from wwpdb.apps.validation.src.utils.validation_xml_reader import ValidationXMLReader

from wwpdb.apps.val_rel.ValidateRelease import runValidation
from wwpdb.apps.val_rel.utils.Files import get_gzip_name
from wwpdb.apps.val_rel.utils.FindEntries import FindEntries
from wwpdb.apps.val_rel.utils.mmCIFInfo import is_simple_modification

logger = logging.getLogger(__name__)


class CheckResult:
    def __init__(self, output_folder=None, pdbid=None, emdbid=None, siteID=None):
        self.__output_folder = output_folder
        self.__pdbid = pdbid
        self.__emdbid = emdbid
        self.__siteid = siteID
        self.__message = {}
        self.__prepare_message()
        self.missing_files = {}
        self.validation_xml = None
        self.failed_programs = []

    def __prepare_message(self):
        self.__message["pdbID"] = self.__pdbid
        self.__message["emdbID"] = self.__emdbid
        self.__message['outputRoot'] = self.__output_folder
        if self.__siteid is not None:
            self.__message["siteID"] = self.__siteid


    def check_entry(self):
        self.rv = runValidation()
        self.rv.process_message(self.__message)
        self.rv.set_entry_id()
        self.rv.set_output_dir_and_files()

        model_file = None
        if self.__pdbid:
            model_file = self.rv.getModelPath()
        em_xml_file = None
        if self.__emdbid:
            em_xml_file = self.rv.getEMXMLPath()

        simple_modification = False
        if model_file and not em_xml_file:
            simple_modification = is_simple_modification(model_path=model_file)
        self.validation_xml = get_gzip_name(self.rv.getValidationXml())
        logging.debug('validation xml: {}'.format(self.validation_xml))
        output_file_dict = self.rv.getCoreOutputFileDict()
        logging.debug('output_file_dict')
        logging.debug(output_file_dict)

        if not simple_modification:
            for output_file_type in output_file_dict:
                output_file = output_file_dict[output_file_type]
                gzipped_output_file = get_gzip_name(output_file)
                if not os.path.exists(gzipped_output_file):
                    self.missing_files.setdefault(output_file_type, []).append(
                        {self.rv.getEntryId(): gzipped_output_file})

            self.check_failed_programs()

    def get_missing_files(self):
        return self.missing_files

    def check_failed_programs(self):
        if self.validation_xml:
            if os.path.exists(self.validation_xml):
                vfx = ValidationXMLReader(self.validation_xml)
                self.failed_programs = vfx.get_failed_programs()

    def get_failed_programs(self):
        return self.failed_programs


class CheckEntries:
    def __init__(self, siteID=None):
        self.__siteid = siteID
        self.entry_list = []
        self.return_dictionary = {}
        self.failed_entries = set()
        self.entries_with_failed_programs = []

    def get_entries(self, skip_emdb=False, pdb_entry_file=None, emdb_entry_file=None):
        fe = FindEntries(siteID=self.__siteid)
        pdb_entries = []
        emdb_entries = []

        if pdb_entry_file:
            if os.path.exists(pdb_entry_file):
                with open(pdb_entry_file) as in_file:
                    for pdb_line in in_file:
                        pdb_entries.append(pdb_line.strip())
        else:
            pdb_entries.extend(fe.get_added_pdb_entries())
            pdb_entries.extend(fe.get_modified_pdb_entries())
        if not skip_emdb:
            emdb_entries.extend(fe.get_emdb_entries())
        for pdb_entry in pdb_entries:
            self.entry_list.append((pdb_entry, 'pdb'))
        for emdb_entry in emdb_entries:
            self.entry_list.append((emdb_entry, 'emdb'))

    def check_entries(self, output_folder=None):

        for entry in self.entry_list:
            entry_id = entry[0]
            entry_type = entry[1]
            if entry_type == 'pdb':
                cr = CheckResult(output_folder=output_folder, pdbid=entry_id, siteID=self.__siteid)
            elif entry_type == 'emdb':
                cr = CheckResult(output_folder=output_folder, emdbid=entry_id, siteID=self.__siteid)
            else:
                logging.error('Unknown entry type')
                return {}
            cr.check_entry()
            missing_ret = cr.get_missing_files()
            for missing_type in missing_ret:
                self.return_dictionary.setdefault(entry_type, {}).setdefault(missing_type, []).append(
                    missing_ret[missing_type])
                self.failed_entries.add(entry_id)
            ret_failed = cr.get_failed_programs()
            if ret_failed:
                self.entries_with_failed_programs.append(entry_id)
                for program in ret_failed:
                    self.return_dictionary.setdefault('failed_programs', {}).setdefault(program, []).append(entry_id)

    def get_full_details(self):
        return self.return_dictionary

    def get_entries_with_failed_programs(self):
        return self.entries_with_failed_programs

    def get_failed_entries(self):
        return list(self.failed_entries)

    def write_missing(self, output_file):
        with open(output_file, 'w') as out_file:
            out_file.write('\n'.join(self.get_failed_entries()))


def prepare_entries_and_check(siteID=None, output_folder=None, failed_entries_file=None, skip_emdb=False, pdb_entry_file=None):
    ce = CheckEntries(siteID=siteID)
    ce.get_entries(skip_emdb=skip_emdb, pdb_entry_file=pdb_entry_file)
    ce.check_entries(output_folder=output_folder)
    print('full details of missing entries')
    pprint(ce.get_full_details())
    print('entries with missing output: {}'.format(','.join(ce.get_failed_entries())))
    print('entries with failed programs: {}'.format(','.join(ce.get_entries_with_failed_programs())))

    if failed_entries_file:
        ce.write_missing(failed_entries_file)


def main():
    log_format = "%(funcName)s (%(levelname)s) - %(message)s"
    logging.basicConfig(format=log_format)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d",
        "--debug",
        help="debugging",
        action="store_const",
        dest="loglevel",
        const=logging.DEBUG,
        default=logging.INFO,
    )
    parser.add_argument("--output_root", help="root folder to output check entries", type=str)
    parser.add_argument("--failed_entries_file", help="file to output failed entries", type=str)
    parser.add_argument("--pdb_entry_file", help="file containing PDB entries - one per line", type=str)
    parser.add_argument("--site_id", help="site id to get files from", type=str)
    parser.add_argument('--skip_emdb', action="store_true")
    args = parser.parse_args()
    logger.setLevel(args.loglevel)

    prepare_entries_and_check(siteID=args.site_id, output_folder=args.output_root, failed_entries_file=args.failed_entries_file,
                              skip_emdb=args.skip_emdb, pdb_entry_file=args.pdb_entry_file)


if __name__ == '__main__':
    main()
