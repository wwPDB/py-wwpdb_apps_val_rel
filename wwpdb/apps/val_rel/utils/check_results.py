
import os
import argparse
import logging
from pprint import pprint
from wwpdb.apps.val_rel.ValidateRelease import runValidation
from wwpdb.apps.val_rel.utils.Files import get_gzip_name
from wwpdb.apps.val_rel.utils.FindEntries import FindEntries

logger = logging.getLogger(__name__)

class checkResult:

    def __init__(self, output_folder=None, pdbid=None, emdbid=None):
        self.__output_folder = output_folder
        self.__pdbid = pdbid
        self.__emdbid = emdbid
        self.__message = {}
        self.__prepare_message()
        self.missing_files = {}
        
    def __prepare_message(self):
        self.__message["pdbID"] = self.__pdbid
        self.__message["emdbID"] = self.__emdbid
        self.__message['outputRoot'] = self.__output_folder

    def check_entry(self):
        self.rv = runValidation()
        self.rv.process_message(self.__message)
        self.rv.set_entry_id()
        self.rv.set_output_dir_and_files()
        output_file_dict = self.rv.getCoreOutputFileDict()
    
        for output_file_type in output_file_dict:
            output_file = output_file_dict[output_file_type]
            gzipped_output_file = get_gzip_name(output_file)
            if not os.path.exists(gzipped_output_file):
                self.missing_files.setdefault(output_file_type, []).append({self.rv.getEntryId(): gzipped_output_file})

    def get_missing_files(self):
        return self.missing_files


def run_check(entry_list, entry_type):
    missing_files = {}
    
    for entry in entries_to_check:
        cr = None
        if entry_type == 'pdb':
            cr = checkResult(output_folder=output_folder, pdbid=entry)
        elif entry_file == 'emdb':
            cr = checkResult(output_folder=output_folder, emdbid=entry)
        else:
            logging.error('Unknown entry type')
            return {}
        cr.check_entry()
        ret = cr.get_missing_files()
        for missing_type in ret:
            missing_files.setdefault(missing_type, []).append(ret[missing_type])

    return missing_files
    

def check_entries(output_folder, entry_file=None, entry_list=None, pdbids=True, emdbids=False, pdb_release=False, pdb_modified=False, emdb_release=False):

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
    if pdb_releemdb_releasease:
        entries_to_check.setdefault('emdb', []).extend(fe.get_emdb_entries())

    for entry_type in entries_to_check:
        ret = run_check(entries_to_check[entry_type], entry_type)
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

    check_entries(output_folder=args.output_root, 
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


