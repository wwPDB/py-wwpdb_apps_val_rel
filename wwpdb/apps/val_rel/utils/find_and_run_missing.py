import argparse
import logging

from wwpdb.apps.val_rel.utils.check_results import CheckEntries
from wwpdb.apps.val_rel.PopulateValidateRelease import PopulateValidateRelease

logger = logging.getLogger(__name__)

class FindAndRunMissing:

    def __init__(self):
        self.ce = CheckEntries()
        self.missing_ids = []
        self.missing_file = 'missing.ids'

    def find_missing(self):
        self.ce.get_entries()
        self.ce.check_entries()
        self.missing_ids = self.ce.get_failed_entries()

    def populate_queue(self):
        if self.missing_ids:
            pvr = PopulateValidateRelease(entry_list=self.missing_ids,
                                          validation_sub_dir='missing',
                                          )
            pvr.run_process()

    def run_process(self):
        self.find_missing()
        self.populate_queue()


def main():
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
    args = parser.parse_args()
    logger.setLevel(args.loglevel)

    FindAndRunMissing().run_process()


if "__main__" in __name__:
    main()