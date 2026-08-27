import argparse
import logging
import os
from typing import Dict, List, Optional, Set, Union

from wwpdb.utils.config.ConfigInfo import getSiteId

from wwpdb.apps.val_rel.utils.FindEntries import FindEntries
from wwpdb.apps.val_rel.utils.getFilesRelease import getFilesRelease
from wwpdb.apps.val_rel.utils.mmCIFInfo import mmCIFInfo
from wwpdb.apps.val_rel.utils.outputFiles import outputFiles
from wwpdb.apps.val_rel.utils.XmlInfo import XmlInfo

logger = logging.getLogger(__name__)


class FindAndProcessEntries:
    def __init__(
        self,
        entry_string: str = "",
        entry_list: Optional[List[str]] = None,
        entry_file: str = "",
        skip_emdb: bool = False,
        pdb_release: bool = False,
        emdb_release: bool = False,
        site_id: Optional[str] = None,
        nocache: bool = False,
    ) -> None:  # pylint: disable=unused-argument
        if site_id is None:
            site_id = getSiteId()
        if entry_list is None:
            entry_list = []
        self.__entry_list = entry_list
        self.__entry_string = entry_string
        self.__entry_file = entry_file
        self.__site_id = site_id
        self.__entries: List[str] = []
        self.__pdb_entries: List[str] = []
        self.__emdb_entries: List[str] = []
        self.__all_pdb_entries: Set[str] = set()
        self.__added_entries: List[str] = []
        self.__messages: List[Dict[str, Union[Optional[str], bool]]] = []
        self.__pdb_release = pdb_release
        self.__emdb_release = emdb_release
        self.__skip_emdb = skip_emdb  # pylint: disable=unused-private-member  # Not used right now.
        of = outputFiles(siteID=site_id)

        if nocache:
            self.__cache = None
        else:
            self.__cache = of.get_ftp_cache_folder()

    def find_and_process_entries(self) -> None:
        self.find_onedep_entries()
        self.process_entry_file()
        self.process_entry_list()
        self.process_entry_string()
        self.categorise_entries()
        self.process_emdb_entries()
        self.process_pdb_entries()

    def run_process(self) -> None:
        self.find_and_process_entries()

    def find_onedep_entries(self) -> None:
        fe = FindEntries(siteID=self.__site_id)
        if self.__pdb_release:
            self.__pdb_entries.extend(fe.get_added_pdb_entries())
            self.__pdb_entries.extend(fe.get_modified_pdb_entries())
            self.__all_pdb_entries = set(self.__pdb_entries[:])
        if self.__emdb_release:
            self.__emdb_entries.extend(fe.get_emdb_entries())

    def process_entry_file(self) -> None:
        if self.__entry_file:
            if os.path.exists(self.__entry_file):
                with open(self.__entry_file) as inFile:
                    for file_line in inFile:
                        self.__entries.append(file_line.strip())
            else:
                logger.error("file: %s not found", self.__entry_file)

    def process_entry_list(self) -> None:
        if self.__entry_list:
            logger.info("entries from input list: %s", self.__entry_list)
            self.__entries.extend(self.__entry_list)

    def process_entry_string(self) -> None:
        if self.__entry_string:
            entries_from_entry_string = self.__entry_string.split(",")
            logger.info("entries from input string: %s", entries_from_entry_string)
            self.__entries.extend(entries_from_entry_string)

    def categorise_entries(self) -> None:
        for entry in self.__entries:
            if "EMD-" in entry.upper():
                self.__emdb_entries.append(entry)
            else:
                self.__pdb_entries.append(entry)

    def process_emdb_entries(self) -> None:
        for emdb_entry in self.__emdb_entries:
            if emdb_entry not in self.__added_entries:
                # stop duplication of making EM validation reports twice
                logger.debug(emdb_entry)
                try:
                    re = getFilesRelease(siteID=self.__site_id, emdb_id=emdb_entry, pdb_id=None, cache=self.__cache)
                    em_xml = re.get_emdb_xml()

                    em_vol = re.get_emdb_volume()
                    if em_vol.path:
                        logger.debug("using XML: %s", em_xml.path)
                        if em_xml.path is None:
                            logger.warning("No EMDB XML file found for %s", emdb_entry)
                            continue
                        pdbids = XmlInfo(em_xml.path).get_pdbids_from_xml()
                        if pdbids:
                            logger.info("PDB entries associated with %s: %s", emdb_entry, ",".join(pdbids))
                            for pdb_id in pdbids:
                                pdbid = pdb_id.lower()
                                re.set_pdb_id(pdb_id=pdbid)
                                model = re.get_model()
                                pdb_file = model.path
                                if pdb_file:
                                    cf = mmCIFInfo(pdb_file)
                                    associated_emdb = cf.get_associated_emdb()
                                    if associated_emdb == emdb_entry:
                                        if pdbid in self.__pdb_entries:
                                            logger.info(
                                                "removing %s from the PDB queue to stop duplication of report generation",
                                                pdbid,
                                            )
                                            self.__pdb_entries.remove(pdbid)
                                        else:
                                            self.__all_pdb_entries.add(pdbid)
                                    # what if its not? should it be added to the queue?
                                elif pdbid in self.__pdb_entries:
                                    logger.info("removing %s as pdb file does not exist", pdbid)
                                    self.__pdb_entries.remove(pdbid)

                        message: Dict[str, Union[Optional[str], bool]] = {"emdbID": emdb_entry}
                        self.__messages.append(message)
                        self.__added_entries.append(emdb_entry)
                    re.remove_local_temp_files()
                except:  # noqa: E722,BLE001 pylint: disable=bare-except
                    logger.exception("ERROR processing %s", emdb_entry)

    def process_pdb_entries(self) -> None:
        for pdb_entry in self.__pdb_entries:
            if pdb_entry not in self.__added_entries:
                message: Dict[str, Union[Optional[str], bool]] = {"pdbID": pdb_entry}
                self.__messages.append(message)
                self.__added_entries.append(pdb_entry)

    def get_found_entries(self) -> List[Dict[str, Union[Optional[str], bool]]]:
        return self.__messages

    def get_pdb_entries(self) -> List[str]:
        """Returns list of PDB entries as a list -- might have duplicates"""
        return self.__pdb_entries

    def get_emdb_entries(self) -> List[str]:
        return self.__emdb_entries

    def get_all_pdb_entries(self) -> Set[str]:
        """Returns the unique set of pdb_entries"""
        return self.__all_pdb_entries

    def get_added_entries(self) -> List[str]:
        return self.__added_entries

    def add_message(self, message: Dict[str, Union[Optional[str], bool]]) -> None:
        self.__messages.append(message)

    def add_entry(self, entry: str) -> None:
        """Adds an entry to the list of added added entries"""
        self.__added_entries.append(entry)


def main() -> None:
    # Create logger -
    logger = logging.getLogger()  # pylint: disable=redefined-outer-name
    FORMAT = "[%(asctime)s %(levelname)s]-%(module)s.%(funcName)s: %(message)s"
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
    parser.add_argument("--entry_list", help="comma separated list of entries", type=str)
    parser.add_argument("--entry_file", help="file containing list of entries - one per line", type=str)
    parser.add_argument("--pdb_release", help="run PDB entries scheduled for release", action="store_true")
    parser.add_argument("--emdb_release", help="run EMDB entries scheduled for release", action="store_true")
    parser.add_argument("--skip_emdb", help="skip emdb validation report calculation", action="store_true")
    parser.add_argument("--siteID", help="siteID", type=str, default=getSiteId())
    parser.add_argument("--nocache", help="Do not use the FTP cache", action="store_true")
    args = parser.parse_args()
    logger.setLevel(args.loglevel)

    fape = FindAndProcessEntries(
        entry_string=args.entry_list,
        entry_file=args.entry_file,
        pdb_release=args.pdb_release,
        emdb_release=args.emdb_release,
        site_id=args.siteID,
        skip_emdb=args.skip_emdb,
        nocache=args.nocache,
    )

    fape.run_process()
    # return fape.messages ---- Is this correct? Should it be printed to stdout or written to a file? For now, just print it.


if "__main__" in __name__:
    main()
