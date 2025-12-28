import argparse
import logging
import os

from wwpdb.utils.config.ConfigInfo import getSiteId

from wwpdb.apps.val_rel.utils.FindEntries import FindEntries
from wwpdb.apps.val_rel.utils.XmlInfo import XmlInfo
from wwpdb.apps.val_rel.utils.getFilesRelease import getFilesRelease
from wwpdb.apps.val_rel.utils.mmCIFInfo import mmCIFInfo
from wwpdb.apps.val_rel.utils.outputFiles import outputFiles

logger = logging.getLogger(__name__)


class FindAndProcessEntries:

    def __init__(self, entry_string='', entry_list=[], entry_file='',
                 skip_emdb=False,
                 pdb_release=False, emdb_release=False,
                 site_id=getSiteId(),
                 nocache=False):
        self.entry_list = entry_list
        self.entry_string = entry_string
        self.entry_file = entry_file
        self.site_id = site_id
        self.entries = []
        self.pdb_entries = []
        self.emdb_entries = []
        self.all_pdb_entries = set()
        self.added_entries = []
        self.messages = []
        self.pdb_release = pdb_release
        self.emdb_release = emdb_release
        self.skip_emdb = skip_emdb
        self.__nocache = nocache
        of = outputFiles(siteID=site_id)

        if nocache:
            self.__cache = None
        else:
            self.__cache = of.get_ftp_cache_folder()

    def find_and_process_entries(self):
        self.find_onedep_entries()
        self.process_entry_file()
        self.process_entry_list()
        self.process_entry_string()
        self.categorise_entries()
        self.process_emdb_entries()
        self.process_pdb_entries()

    def run_process(self):
        self.find_and_process_entries()

    def find_onedep_entries(self):
        fe = FindEntries(siteID=self.site_id)
        if self.pdb_release:
            self.pdb_entries.extend(fe.get_added_pdb_entries())
            self.pdb_entries.extend(fe.get_modified_pdb_entries())
            self.all_pdb_entries = set(self.pdb_entries[:])
        if self.emdb_release:
            self.emdb_entries.extend(fe.get_emdb_entries())

    def process_entry_file(self):
        if self.entry_file:
            if os.path.exists(self.entry_file):
                with open(self.entry_file) as inFile:
                    for file_line in inFile:
                        self.entries.append(file_line.strip())
            else:
                logging.error("file: %s not found", self.entry_file)

    def process_entry_list(self):
        if self.entry_list:
            logging.info('entries from input list: {}'.format(self.entry_list))
            self.entries.extend(self.entry_list)

    def process_entry_string(self):
        if self.entry_string:
            entries_from_entry_string = self.entry_string.split(",")
            logging.info('entries from input string: {}'.format(entries_from_entry_string))
            self.entries.extend(entries_from_entry_string)

    def categorise_entries(self):
        for entry in self.entries:
            if "EMD-" in entry.upper():
                self.emdb_entries.append(entry)
            else:
                self.pdb_entries.append(entry)

    def process_emdb_entries(self):
        for emdb_entry in self.emdb_entries:
            if emdb_entry not in self.added_entries:
                # stop duplication of making EM validation reports twice
                logger.debug(emdb_entry)
                try:
                    re = getFilesRelease(siteID=self.site_id, emdb_id=emdb_entry, pdb_id=None,
                                         cache=self.__cache)
                    em_xml = re.get_emdb_xml()

                    em_vol = re.get_emdb_volume()
                    if em_vol:
                        logger.debug('using XML: %s', em_xml)
                        pdbids = XmlInfo(em_xml).get_pdbids_from_xml()
                        if pdbids:
                            logger.info(
                                "PDB entries associated with %s: %s", emdb_entry, ",".join(pdbids)
                            )
                            for pdbid in pdbids:
                                pdbid = pdbid.lower()
                                re.set_pdb_id(pdb_id=pdbid)
                                pdb_file = re.get_model()
                                if pdb_file:
                                    cf = mmCIFInfo(pdb_file)
                                    associated_emdb = cf.get_associated_emdb()
                                    if associated_emdb == emdb_entry:
                                        if pdbid in self.pdb_entries:
                                            logger.info(
                                                "removing %s from the PDB queue to stop duplication of report generation",
                                                pdbid
                                            )
                                            self.pdb_entries.remove(pdbid)
                                        else:
                                            self.all_pdb_entries.add(pdbid)
                                    # what if its not? should it be added to the queue?
                                else:
                                    if pdbid in self.pdb_entries:
                                        logger.info('removing %s as pdb file does not exist', pdbid)
                                        self.pdb_entries.remove(pdbid)

                        message = {"emdbID": emdb_entry}
                        self.messages.append(message)
                        self.added_entries.append(emdb_entry)
                    re.remove_local_temp_files()
                except:  # noqa: E722,BLE001
                    logger.exception("ERROR processing %s", emdb_entry)

    def process_pdb_entries(self):
        for pdb_entry in self.pdb_entries:
            if pdb_entry not in self.added_entries:
                message = {"pdbID": pdb_entry}
                self.messages.append(message)
                self.added_entries.append(pdb_entry)

    def get_found_entries(self):
        return self.messages

    def get_pdb_entries(self):
        return self.pdb_entries

    def get_emdb_entries(self):
        return self.emdb_entries


def main():
    # Create logger -
    logger = logging.getLogger()
    FORMAT = '[%(asctime)s %(levelname)s]-%(module)s.%(funcName)s: %(message)s'
    logging.basicConfig(format=FORMAT)

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
    parser.add_argument(
        "--entry_list", help="comma separated list of entries", type=str
    )
    parser.add_argument(
        "--entry_file", help="file containing list of entries - one per line", type=str
    )
    parser.add_argument(
        "--pdb_release", help="run PDB entries scheduled for release", action="store_true"
    )
    parser.add_argument(
        "--emdb_release", help="run EMDB entries scheduled for release", action="store_true"
    )
    parser.add_argument(
        "--skip_emdb", help="skip emdb validation report calculation", action="store_true"
    )
    parser.add_argument("--siteID", help="siteID", type=str, default=getSiteId())
    parser.add_argument(
        "--nocache", help="Do not use the FTP cache", action="store_true"
    )
    args = parser.parse_args()
    logger.setLevel(args.loglevel)

    fape = FindAndProcessEntries(entry_string=args.entry_list,
                                 entry_file=args.entry_file,
                                 pdb_release=args.pdb_release,
                                 emdb_release=args.emdb_release,
                                 site_id=args.siteID,
                                 skip_emdb=args.skip_emdb,
                                 nocache=args.nocache)

    fape.run_process()
    return fape.messages


if "__main__" in __name__:
    main()
