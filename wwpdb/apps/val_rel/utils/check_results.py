
import os
import argparse
import logging
from pprint import pprint
from wwpdb.apps.val_rel.ValidateRelease import runValidation
from wwpdb.apps.val_rel.utils.Files import get_gzip_name
from wwpdb.apps.val_rel.utils.FindEntries import FindEntries
from wwpdb.apps.validation.src.utils.validation_xml_reader import ValidationXMLReader

logger = logging.getLogger(__name__)

class checkResult:

    def __init__(self, output_folder=None, pdbid=None, emdbid=None):
        self.__output_folder = output_folder
        self.__pdbid = pdbid
        self.__emdbid = emdbid
        self.__message = {}
        self.__prepare_message()
        self.missing_files = {}
        self.validation_xml = None
        self.failed_programs = []
        
    def __prepare_message(self):
        self.__message["pdbID"] = self.__pdbid
        self.__message["emdbID"] = self.__emdbid
        self.__message['outputRoot'] = self.__output_folder

    def check_entry(self):
        self.rv = runValidation()
        self.rv.process_message(self.__message)
        self.rv.set_entry_id()
        self.rv.set_output_dir_and_files()
        self.validation_xml = get_gzip_name(self.rv.getValidationXml())
        logging.debug('validation xml: {}'.format(self.validation_xml))
        output_file_dict = self.rv.getCoreOutputFileDict()
        logging.debug('output_file_dict')
        logging.debug(output_file_dict)

        for output_file_type in output_file_dict:
            output_file = output_file_dict[output_file_type]
            gzipped_output_file = get_gzip_name(output_file)
            if not os.path.exists(gzipped_output_file):
                self.missing_files.setdefault(output_file_type, []).append({self.rv.getEntryId(): gzipped_output_file})
        
        self.check_failed_programs()

    def get_missing_files(self):
        return self.missing_files

    def check_failed_programs(self):
        if self.validation_xml:
            vfx = ValidationXMLReader(self.validation_xml)
            self.failed_programs = vfx.get_failed_programs()

    def get_failed_programs(self):
        return self.failed_programs

def check_entries(entry_list, entry_type, output_folder=None):
    ret = {}
    
    for entry in entry_list:
        cr = None
        if entry_type == 'pdb':
            cr = checkResult(output_folder=output_folder, pdbid=entry)
        elif entry_file == 'emdb':
            cr = checkResult(output_folder=output_folder, emdbid=entry)
        else:
            logging.error('Unknown entry type')
            return {}
        cr.check_entry()
        missing_ret = cr.get_missing_files()
        for missing_type in missing_ret:
            ret.setdefault(missing_type, []).append(missing_ret[missing_type])
        ret_failed = cr.get_failed_programs()
        if ret_failed:
            for program in ret_failed:
                ret.setdefault('failed_programs', {}).setdefault(program, []).append(entry)

    return ret
    

def prepare_entries_and_check(output_folder=None, entry_file=None, entry_list=None, pdbids=True, emdbids=False, pdb_release=False, pdb_modified=False, emdb_release=False):

    entries_to_check = {}
    fe = FindEntries()
    missing_files = {}
    
    if entry_file:
        with open(entry_file) as entryFile:
            for line in entryFile:
                if line:
                    entry = line.strip()
                    if pdbids:
                        entries_to_check.setdefault('pdb', []).append(entry)
                    else:
                        entries_to_check.setdefault('emdb', []).append(entry)
    if entry_list:
        if pdbids:
            entries_to_check.setdefault('pdb', []).extend(entry_list)
        else:
            entries_to_check.setdefault('pdb', []).extend(entry_list)

    if pdb_release:
        entries_to_check.setdefault('pdb', []).extend(fe.get_added_pdb_entries())
    if pdb_modified:
        entries_to_check.setdefault('pdb', []).extend(fe.get_modified_pdb_entries())
    if emdb_release:
        entries_to_check.setdefault('emdb', []).extend(fe.get_emdb_entries())

    for entry_type in entries_to_check:
        ret = check_entries(entries_to_check[entry_type], entry_type, output_folder=output_folder)
        missing_files[entry_type] = ret

    pprint(missing_files)


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
    parser.add_argument("--entries", help="list of entries", type=str)
    parser.add_argument(
        "--entry_file", help="site id to get python code from", type=str
    )
    parser.add_argument(
        "--pdbids", help="entries are pdbids", action="store_true"
    )
    parser.add_argument(
        "--emdbids", help="entries are emdbids", action="store_true"
    )
    parser.add_argument(
        "--pdb_release", help="find PDB entries scheduled for new release", action="store_true"
    )
    parser.add_argument(
        "--pdb_modified",
        help="find PDB entries scheduled for modified release",
        action="store_true",
    )
    parser.add_argument(
        "--emdb_release",
        help="find EMDB entries scheduled for release",
        action="store_true",
    )
    args = parser.parse_args()
    logger.setLevel(args.loglevel)

    prepare_entries_and_check(output_folder=args.output_root, 
                  entry_file=args.entry_file, 
                  entry_list=args.entries, 
                  pdbids=args.pdbids, 
                  emdbids=args.emdbids,
                  pdb_release=args.pdb_release,
                  pdb_modified=args.pdb_modified,
                  emdb_release=args.emdb_release
                  )

if __name__ == '__main__':
    main()


