import argparse
import logging
import os
import shutil
from typing import List, Optional, Set

from wwpdb.utils.config.ConfigInfo import getSiteId

from wwpdb.apps.val_rel.utils.FindAndProcessEntries import FindAndProcessEntries
from wwpdb.apps.val_rel.utils.outputFiles import outputFiles

logger = logging.getLogger(__name__)


class FindExcessEntries:
    def __init__(self, site_id: Optional[str] = None, dry_run: bool = False) -> None:
        if site_id is None:
            site_id = getSiteId()
        self.site_id = site_id
        self.dry_run = dry_run
        self.pdb_entries: Set[str] = set()
        self.emdb_entries: List[str] = []
        self.output_pdb_entries: List[str] = []
        self.output_emdb_entries: List[str] = []

    def run_process(self) -> None:
        self.find_pdb_and_emdb_entries()
        self.find_pdb_output_entries()
        self.find_emdb_output_entries()
        self.check_pdb_entries_output_should_exist()

    def find_pdb_and_emdb_entries(self) -> None:
        pvr = FindAndProcessEntries(
            pdb_release=True,
            emdb_release=True,
            site_id=self.site_id,
        )
        pvr.find_onedep_entries()
        pvr.process_emdb_entries()
        pvr.process_pdb_entries()
        self.pdb_entries = pvr.all_pdb_entries
        self.emdb_entries = pvr.emdb_entries

    def get_pdb_output_folder(self) -> str:
        return outputFiles(siteID=self.site_id).get_pdb_root_folder()

    def get_emdb_output_folder(self) -> str:
        return outputFiles(siteID=self.site_id).get_emdb_root_folder()

    def find_pdb_output_entries(self) -> None:
        self.output_pdb_entries = os.listdir(self.get_pdb_output_folder())

    def find_emdb_output_entries(self) -> None:
        self.output_emdb_entries = os.listdir(self.get_emdb_output_folder())

    def check_pdb_entries_output_should_exist(self) -> None:
        for entry in self.output_pdb_entries:
            logger.info(entry)
            if entry not in self.pdb_entries:
                logger.info("%s should be removed", entry)
                path_to_remove = os.path.join(self.get_pdb_output_folder(), entry)
                logger.info("%s being removed", path_to_remove)
                if not self.dry_run:
                    shutil.rmtree(path_to_remove, ignore_errors=True)


def main() -> None:
    # Create logger -
    FORMAT = "[%(asctime)s %(levelname)s]-%(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(format=FORMAT)
    logger.setLevel(logging.DEBUG)

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
    parser.add_argument("--siteID", help="siteID", type=str, default=getSiteId())
    parser.add_argument("--dry_run", help="do a dry run", action="store_true")
    args = parser.parse_args()
    logger.setLevel(args.loglevel)

    fee = FindExcessEntries(site_id=args.siteID, dry_run=args.dry_run)
    fee.run_process()


if "__main__" in __name__:
    main()
