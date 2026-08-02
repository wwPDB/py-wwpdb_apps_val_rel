import argparse
import csv
import json
import logging
import os
from pprint import pformat, pprint
from typing import Dict, List, Optional, Set, Tuple, Union, cast

from wwpdb.apps.validation.src.utils.validation_xml_reader import ValidationXMLReader
from wwpdb.io.locator.ReleasePathInfo import ReleasePathInfo

from wwpdb.apps.val_rel.utils.Files import get_gzip_name
from wwpdb.apps.val_rel.utils.FindEntries import FindEntries
from wwpdb.apps.val_rel.utils.mmCIFInfo import is_simple_modification
from wwpdb.apps.val_rel.ValidateRelease import runValidation

# We replace with root if main
logger = logging.getLogger(__name__)


class CheckResult:
    def __init__(
        self,
        output_folder: Optional[str] = None,
        pdbid: Optional[str] = None,
        emdbid: Optional[str] = None,
        siteID: Optional[str] = None,
        validation_sub_folder: str = "current",
    ) -> None:
        self.__output_folder = output_folder
        self.__pdbid = pdbid
        self.__emdbid = emdbid
        self.__siteid = siteID
        self.__validation_sub_folder = validation_sub_folder
        self.__message: Dict[str, Union[Optional[str], bool]] = {}
        self.__prepare_message()
        self.__expected_files: Dict[str, str] = {}
        self.__missing_files: Dict[str, List[Dict[str, str]]] = {}
        self.__validation_xml: Optional[str] = None
        self.__failed_programs: List[str] = []

    def __prepare_message(self) -> None:
        self.__message["pdbID"] = self.__pdbid
        self.__message["emdbID"] = self.__emdbid
        self.__message["outputRoot"] = self.__output_folder
        if self.__siteid is not None:
            self.__message["siteID"] = self.__siteid
        self.__message["subfolder"] = self.__validation_sub_folder

    def is_expected_file_type(self, file_type: str) -> bool:
        if not self.__pdbid and self.__emdbid:
            expected_missing_file_types = ["svg", "png"]
            if file_type in expected_missing_file_types:
                return False
        return True

    def check_entry(self) -> None:
        self.rv = runValidation()  # pylint: disable=attribute-defined-outside-init
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
        self.__validation_xml = get_gzip_name(self.rv.getValidationXml())
        logger.debug("validation xml: %s", self.__validation_xml)
        output_files = self.rv.getCoreOutputFileDict()
        logger.debug("output_file_dict")
        logger.debug(self.__expected_files)

        if not simple_modification:
            for output_file_type in output_files:
                output_file = output_files[output_file_type]
                gzipped_output_file = get_gzip_name(output_file)
                if self.is_expected_file_type(output_file_type):
                    self.__expected_files[output_file_type] = gzipped_output_file
                    if not os.path.exists(gzipped_output_file):
                        self.__missing_files.setdefault(output_file_type, []).append(
                            {cast("str", self.rv.getEntryId()): gzipped_output_file}
                        )

            self.check_failed_programs()

    def get_missing_files(self) -> Dict[str, List[Dict[str, str]]]:
        #  {'pdf': [{'9bgf': '/wwpdb_da/da_top/data_devel/for_release/val_reports/current/9bgf/9bgf_validation.pdf.gz'}], ...
        return self.__missing_files

    def get_expected_files(self) -> Dict[str, str]:
        return self.__expected_files

    def did_all_files_fail(self) -> bool:
        """Returns true if none of the expected files are found"""
        if self.__missing_files:
            if len(self.__expected_files) - len(self.__missing_files) == 0:
                return True
        return False

    def check_failed_programs(self) -> None:
        """If a validation_xml file exists, parse file and set self.__failed_programs"""
        if self.__validation_xml:
            if os.path.exists(self.__validation_xml):
                vfx = ValidationXMLReader(self.__validation_xml)
                self.__failed_programs = vfx.get_failed_programs()

    def get_failed_programs(self) -> List[str]:
        return self.__failed_programs


class CheckEntries:
    def __init__(self, siteID: Optional[str] = None) -> None:
        self.__siteid = siteID
        self.entry_list: List[Tuple[str, str]] = []  # List of (entry_id, "emdb"/"pdb")
        self.return_dictionary: Dict[str, Dict[str, Union[List[str], Dict[str, List[List[Dict[str, str]]]]]]] = {}
        # {'missing_output': {'pdb': {'pdf': [[{'0304': '/wwpdb_da/da_top/data_devel/for_release/val_reports/current/0304/0304_validation.pdf.gz'}], ...
        # {'failed_programs': {'molprobity': ['1abc']}}
        self.failed_entries: Dict[str, Set[str]] = {}
        self.entries_with_failed_programs: List[str] = []
        self.rpi = ReleasePathInfo(siteId=self.__siteid)

    def clear_entry_list(self) -> None:
        self.entry_list = []
        self.return_dictionary = {}
        self.failed_entries = {}
        self.entries_with_failed_programs = []

    def get_missing_file_path(self) -> str:
        return os.path.join(self.rpi.get_for_release_path(), "missing.ids")

    def read_missing_file(self) -> List[str]:
        missing_entries: List[str] = []
        entries_to_add: Dict[str, List[str]] = {}
        if os.path.exists(self.get_missing_file_path()):
            with open(self.get_missing_file_path()) as csvfile:
                try:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        entry_id = row["entry_id"]
                        entry_type = row["entry_type"]
                        # entry_row = {'entry_type': entry_type,
                        #              'entry_id': entry_id}
                        missing_entries.append(entry_id)
                        entries_to_add.setdefault(entry_type, []).append(entry_id)
                except Exception:  # noqa: E722,BLE001
                    logger.error("unable to read: %s", self.get_missing_file_path())
        if entries_to_add:
            for entry_type, ents in entries_to_add.items():
                if entry_type == "emdb":
                    self.add_emdb_entries(emdb_entries=ents)
                if entry_type == "pdb":
                    self.add_pdb_entries(pdb_entries=ents)

        logger.info("There are %s entries to check from the missing folder", len(missing_entries))

        return missing_entries

    def write_missing_file(self) -> None:
        logger.info("writing out: %s", self.get_missing_file_path())
        with open(self.get_missing_file_path(), "w") as out_file:
            if self.failed_entries:
                logger.info(pformat(self.failed_entries))
                fieldnames = ["entry_type", "entry_id"]
                writer = csv.DictWriter(out_file, fieldnames=fieldnames)
                writer.writeheader()
                for entry_type in self.failed_entries:
                    for entry_id in self.failed_entries[entry_type]:
                        entry_row = {"entry_type": entry_type, "entry_id": entry_id}
                        writer.writerow(entry_row)

    def get_entries(
        self, skip_emdb: bool = False, pdb_entry_file: Optional[str] = None, emdb_entry_file: Optional[str] = None
    ) -> None:
        fe = FindEntries(siteID=self.__siteid)
        pdb_entries = []
        emdb_entries = []

        if pdb_entry_file or emdb_entry_file:
            if pdb_entry_file:
                if os.path.exists(pdb_entry_file):
                    with open(pdb_entry_file) as in_file:
                        for pdb_line in in_file:
                            pdb_entries.append(pdb_line.strip())
            if emdb_entry_file:
                if os.path.exists(emdb_entry_file):
                    with open(emdb_entry_file) as in_file:
                        for emdb_line in in_file:
                            emdb_entries.append(emdb_line.strip())
        else:
            pdb_entries.extend(fe.get_added_pdb_entries())
            pdb_entries.extend(fe.get_modified_pdb_entries())
            if not skip_emdb:
                emdb_entries.extend(fe.get_emdb_entries())

        self.add_pdb_entries(pdb_entries=pdb_entries)
        self.add_emdb_entries(emdb_entries=emdb_entries)

    def add_emdb_entries(self, emdb_entries: List[str]) -> None:
        logger.info("There are %s EMDB entries to check", len(emdb_entries))
        for emdb_entry in emdb_entries:
            self.entry_list.append((emdb_entry, "emdb"))

    def add_pdb_entries(self, pdb_entries: List[str]) -> None:
        logger.info("There are %s PDB entries to check", len(pdb_entries))
        for pdb_entry in pdb_entries:
            self.entry_list.append((pdb_entry, "pdb"))

    def check_entries(
        self, output_folder: Optional[str] = None, validation_sub_folder: str = "current"
    ) -> Dict[str, str]:  # Always empty
        if self.entry_list:
            for entry in self.entry_list:
                entry_id = entry[0]
                entry_type = entry[1]
                if entry_type == "pdb":
                    cr = CheckResult(
                        output_folder=output_folder,
                        pdbid=entry_id,
                        siteID=self.__siteid,
                        validation_sub_folder=validation_sub_folder,
                    )
                elif entry_type == "emdb":
                    cr = CheckResult(
                        output_folder=output_folder,
                        emdbid=entry_id,
                        siteID=self.__siteid,
                        validation_sub_folder=validation_sub_folder,
                    )
                else:
                    logger.error("Unknown entry type")
                    return {}
                cr.check_entry()
                if cr.did_all_files_fail():
                    self.failed_entries.setdefault(entry_type, set()).add(entry_id)

                missing_ret = cr.get_missing_files()  # dict[str, list[dict[str, str]]]
                for missing_type in missing_ret:
                    cast(
                        "Dict[str, Dict[str, Dict[str, List[List[Dict[str, str]]]]]]", self.return_dictionary
                    ).setdefault("missing_output", {}).setdefault(entry_type, {}).setdefault(missing_type, []).append(
                        missing_ret[missing_type]
                    )

                ret_failed = cr.get_failed_programs()
                if ret_failed:
                    self.entries_with_failed_programs.append(entry_id)
                    for program in ret_failed:
                        cast("Dict[str, Dict[str, List[str]]]", self.return_dictionary).setdefault(
                            "failed_programs", {}
                        ).setdefault(program, []).append(entry_id)
        return {}

    def get_full_details(self) -> Dict[str, Dict[str, Union[List[str], Dict[str, List[List[Dict[str, str]]]]]]]:
        return self.return_dictionary

    def get_failed_programs(self) -> Dict[str, List[str]]:
        return cast("Dict[str, List[str]]", self.return_dictionary.get("failed_programs", {}))

    def get_missing_output(self) -> Dict[str, Dict[str, List[List[Dict[str, str]]]]]:
        return cast("Dict[str, Dict[str, Dict[str, List[List[Dict[str, str]]]]]]", self.return_dictionary).get(
            "missing_output", {}
        )

    def get_entries_with_failed_programs(self) -> List[str]:
        return self.entries_with_failed_programs

    def get_failed_entries(self) -> Dict[str, Set[str]]:
        return self.failed_entries

    def get_entry_list(self) -> List[Tuple[str, str]]:
        return self.entry_list

    def write_missing_json(self, output_file: str) -> None:
        with open(output_file, "w") as out_file:
            json.dump(self.get_failed_entries(), out_file)

    def write_missing(self, output_file: str) -> None:
        with open(output_file, "w") as out_file:
            for entry_type in self.get_failed_entries():
                entries = self.get_failed_entries()[entry_type]
                out_file.write("\n".join(list(entries)))
                out_file.write("\n")


def prepare_entries_and_check(
    siteID: Optional[str] = None,
    output_folder: Optional[str] = None,
    failed_entries_file: Optional[str] = None,
    skip_emdb: bool = False,
    pdb_entry_file: Optional[str] = None,
    emdb_entry_file: Optional[str] = None,
    validation_sub_folder: Optional[str] = None,
) -> None:
    ce = CheckEntries(siteID=siteID)
    failed_entries = {}
    failed_programs = {}
    full_details = {}
    if output_folder:
        ce.get_entries(skip_emdb=skip_emdb, pdb_entry_file=pdb_entry_file, emdb_entry_file=emdb_entry_file)
        ce.check_entries(output_folder=output_folder)
        failed_entries["output"] = ce.get_failed_entries()
        failed_programs["output"] = ce.get_failed_programs()
        full_details["output"] = ce.get_full_details()
    else:
        check_folders = ["current", "missing"]
        if validation_sub_folder:
            check_folders = [validation_sub_folder]
        for sub_folder in check_folders:
            ce.clear_entry_list()
            if pdb_entry_file or emdb_entry_file:
                ce.get_entries(skip_emdb=skip_emdb, pdb_entry_file=pdb_entry_file, emdb_entry_file=emdb_entry_file)
            elif sub_folder == "current":
                ce.get_entries()
            else:
                ce.read_missing_file()
            ce.check_entries(validation_sub_folder=sub_folder)
            failed_entries[sub_folder] = ce.get_failed_entries()
            failed_programs[sub_folder] = ce.get_failed_programs()
            full_details[sub_folder] = ce.get_full_details()

    pprint(full_details)

    if failed_programs:
        for sub_folder in failed_programs:
            for program_type in failed_programs.get(sub_folder, {}):
                entries = list(failed_programs[sub_folder][program_type])
                print("\n%s %s entries with failed programs", sub_folder, program_type)
                print(",".join(entries))

    if failed_entries:
        for sub_folder in failed_entries:
            for entry_type in failed_entries.get(sub_folder, {}):
                entries = list(failed_entries[sub_folder][entry_type])
                print("\n%s %s entries with missing output files", sub_folder, entry_type.upper())
                print(",".join(entries))

    if failed_entries_file:
        ce.write_missing(failed_entries_file)


def main() -> None:
    logger = logging.getLogger()  # pylint: disable=redefined-outer-name
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
    parser.add_argument("--emdb_entry_file", help="file containing EMDB entries - one per line", type=str)
    parser.add_argument("--site_id", help="site id to get files from", type=str)
    parser.add_argument(
        "--validation_sub_folder", help="validation sub directory to check", type=str, default="current"
    )
    parser.add_argument("--skip_emdb", action="store_true")
    args = parser.parse_args()
    logger.setLevel(args.loglevel)

    prepare_entries_and_check(
        siteID=args.site_id,
        output_folder=args.output_root,
        failed_entries_file=args.failed_entries_file,
        skip_emdb=args.skip_emdb,
        pdb_entry_file=args.pdb_entry_file,
        emdb_entry_file=args.emdb_entry_file,
        validation_sub_folder=args.validation_sub_folder,
    )


if __name__ == "__main__":
    main()
