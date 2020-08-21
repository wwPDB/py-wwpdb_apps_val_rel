import argparse
import logging
import os

from wwpdb.apps.val_rel.PopulateValidateRelease import PopulateValidateRelease
from wwpdb.apps.val_rel.utils.check_results import CheckEntries
from wwpdb.io.locator.ReleasePathInfo import ReleasePathInfo

# We replace with root if main
logger = logging.getLogger(__name__)


class FindAndRunMissing:

    def __init__(self, write_missing=False, read_missing=True, siteID=None):
        self.__siteid = siteID
        self.ce = CheckEntries(siteID=self.__siteid)
        self.missing_ids = []
        self.missing_file = 'missing.ids'
        self.rpi = ReleasePathInfo(siteId=self.__siteid)
        self.write_missing = write_missing
        self.read_missing = read_missing

    def find_missing(self):
        self.ce.get_entries()
        self.ce.check_entries()
        self.missing_ids = self.ce.get_failed_entries()

    def get_missing_file_path(self):
        return os.path.join(self.rpi.get_for_release_path(), 'missing.ids')

    def write_out_missing(self):
        if self.missing_ids:
            with open(self.get_missing_file_path(), 'w') as out_file:
                for missing_id in self.missing_ids:
                    out_file.write("%s\n" % missing_id)

    def read_missing_file(self):
        with open(self.get_missing_file_path()) as in_file:
            for file_line in in_file:
                self.missing_ids.append(file_line.strip())

    def populate_queue(self):
        if self.missing_ids:
            pvr = PopulateValidateRelease(entry_list=self.missing_ids,
                                          validation_sub_dir='missing',
                                          site_id=self.__siteid
                                          )
            pvr.run_process()

    def run_process(self):
        if self.read_missing:
            self.read_missing_file()
        else:
            self.find_missing()
        if self.write_missing:
            self.write_out_missing()
        else:
            self.populate_queue()


def main():
    # Root logger
    logger = logging.getLogger()
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
    parser.add_argument('--write_missing', action="store_true")
    parser.add_argument('--read_missing', action="store_true")
    parser.add_argument("--site_id", help="site id to get files from", type=str)

    args = parser.parse_args()
    logger.setLevel(args.loglevel)

    frm = FindAndRunMissing(write_missing=args.write_missing,
                            read_missing=args.read_missing,
                            siteID=args.site_id)
    frm.run_process()


if "__main__" in __name__:
    main()
