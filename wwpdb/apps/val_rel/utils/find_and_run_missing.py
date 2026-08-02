import argparse
import logging
from typing import List, Optional

from wwpdb.apps.val_rel.PopulateValidateRelease import PopulateValidateRelease
from wwpdb.apps.val_rel.utils.check_results import CheckEntries

# We replace with root if main
logger = logging.getLogger(__name__)


class FindAndRunMissing:
    def __init__(
        self,
        write_missing: bool = False,
        read_missing: bool = True,
        siteID: Optional[str] = None,
        priority: bool = False,
    ) -> None:
        self.__siteid = siteID
        self.ce = CheckEntries(siteID=self.__siteid)
        self.__missing_ids: List[str] = []
        self.__write_missing = write_missing
        self.__read_missing = read_missing
        self.__priority = priority

    def find_missing(self) -> None:
        self.ce.get_entries()
        self.ce.check_entries()
        failed_entries = self.ce.get_failed_entries()
        logger.debug("failed_entries")
        logger.debug(failed_entries)

    def __write_out_missing(self) -> None:
        """Writes out the list of missing ids.
        If the list is empty - create empty file to prevent reruns the following week
        """
        self.ce.write_missing_file()

    def __read_missing_file(self) -> None:
        self.__missing_ids = self.ce.read_missing_file()
        logger.debug("missing IDs: %s", ",".join(self.__missing_ids))

    def __populate_queue(self) -> None:
        if self.__missing_ids:
            pvr = PopulateValidateRelease(
                entry_list=self.__missing_ids,
                validation_sub_dir="missing",
                site_id=self.__siteid,
                always_recalculate=True,
                nocache=True,
                priority=self.__priority,
            )
            pvr.run_process()

    def run_process(self) -> None:
        if self.__read_missing:
            self.__read_missing_file()
            self.__populate_queue()
        if self.__write_missing:
            self.find_missing()
            self.__write_out_missing()


def main() -> None:
    # Root logger
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

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write_missing", action="store_true")
    group.add_argument("--read_missing", action="store_true")

    parser.add_argument("--site_id", help="site id to get files from", type=str)

    parser.add_argument("--priority", action="store_true", help="queues are priority queues")

    args = parser.parse_args()
    logger.setLevel(args.loglevel)

    frm = FindAndRunMissing(
        write_missing=args.write_missing, read_missing=args.read_missing, siteID=args.site_id, priority=args.priority
    )
    frm.run_process()


if "__main__" in __name__:
    main()
