import argparse
import json
import logging

from wwpdb.apps.val_rel.config.ValConfig import ValConfig
from wwpdb.utils.config.ConfigInfo import getSiteId
from wwpdb.apps.val_rel.utils.outputFiles import outputFiles
from wwpdb.utils.message_queue.MessagePublisher import MessagePublisher
from wwpdb.apps.val_rel.utils.FindAndProcessEntries import FindAndProcessEntries

logger = logging.getLogger(__name__)


class PopulateValidateRelease:

    def __init__(self, entry_string='', entry_list=[], entry_file='', keep_logs=False, output_root=None,
                 always_recalculate=False, skip_gzip=False, skip_emdb=False, validation_sub_dir='current',
                 pdb_release=False, emdb_release=False,
                 site_id=getSiteId(), nocache=False):
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
        self.keep_logs = keep_logs
        self.output_root = output_root
        self.always_recalculate = always_recalculate
        self.skipGzip = skip_gzip
        self.skip_emdb = skip_emdb
        self.validation_sub_dir = validation_sub_dir
        # Get cachedir
        of = outputFiles(siteID=site_id)
        self.__nocache = nocache
        if nocache:
            self.__cache = None
        else:
            self.__cache = of.get_ftp_cache_folder()

    def find_and_process_entries(self):
        fape = FindAndProcessEntries(entry_string=self.entry_string,
                                     entry_file=self.entry_file,
                                     entry_list=self.entry_list,
                                     skip_emdb=self.skip_emdb,
                                     pdb_release=self.pdb_release,
                                     emdb_release=self.emdb_release,
                                     site_id=self.site_id,
                                     nocache=self.__nocache)
        fape.run_process()
        self.messages = fape.get_found_entries()

    def run_process(self):
        self.find_and_process_entries()
        self.process_messages()

    def process_messages(self):
        if self.messages:
            # Set logging for pika to be lower
            plogging = logging.getLogger('pika')
            plogging.setLevel(logging.ERROR)
            for message in self.messages:

                message["siteID"] = self.site_id
                message["keepLog"] = self.keep_logs
                message['subfolder'] = self.validation_sub_dir
                if self.__nocache:
                    message["nocache"] = self.__nocache
                if self.output_root:
                    message["outputRoot"] = self.output_root
                if self.always_recalculate:
                    message["alwaysRecalculate"] = self.always_recalculate
                if self.skipGzip:
                    message["skipGzip"] = self.skipGzip
                if self.skip_emdb:
                    message['skip_emdb'] = self.skip_emdb
                logger.info('MESSAGE req %s', message)
                vc = ValConfig(self.site_id)
                ok = MessagePublisher().publish(
                    message=json.dumps(message),
                    exchangeName=vc.exchange,
                    queueName=vc.queue_name,
                    routingKey=vc.routing_key,
                )
                logger.info('MESSAGE {}'.format(ok))


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
    parser.add_argument("--keep_logs", help="Keep the log files", action="store_true")
    parser.add_argument(
        "--always_recalculate", help="always recalculate", action="store_true"
    )
    parser.add_argument(
        "--skipGzip", help="skip gizpping output files", action="store_true"
    )
    parser.add_argument(
        "--skip_emdb", help="skip emdb validation report calculation", action="store_true"
    )
    parser.add_argument("--siteID", help="siteID", type=str, default=getSiteId())
    parser.add_argument("--python_siteID", help="siteID for the OneDep code", type=str)
    parser.add_argument("--validation_subdir", help="validation sub directory", type=str, default='current')
    parser.add_argument(
        "--output_root",
        help="Folder to output the results to - overrides default OneDep folders",
        type=str,
    )
    parser.add_argument(
        "--nocache", help="Do not use the FTP cache", action="store_true"
    )
    args = parser.parse_args()
    logger.setLevel(args.loglevel)

    pvr = PopulateValidateRelease(entry_string=args.entry_list,
                                  entry_file=args.entry_file,
                                  pdb_release=args.pdb_release,
                                  emdb_release=args.emdb_release,
                                  site_id=args.siteID,
                                  keep_logs=args.keep_logs,
                                  always_recalculate=args.always_recalculate,
                                  skip_gzip=args.skipGzip,
                                  skip_emdb=args.skip_emdb,
                                  validation_sub_dir=args.validation_subdir,
                                  output_root=args.output_root,
                                  nocache=args.nocache)

    pvr.run_process()


if "__main__" in __name__:
    main()
