import argparse
import json
import logging
import os
import sys

from wwpdb.apps.val_rel.config.ValConfig import ValConfig
from wwpdb.utils.config.ConfigInfo import getSiteId
from wwpdb.apps.val_rel.utils.outputFiles import outputFiles
from wwpdb.utils.message_queue.MessagePublisher import MessagePublisher
from wwpdb.apps.val_rel.utils.FindAndProcessEntries import FindAndProcessEntries
from wwpdb.apps.val_rel.utils.FindEntries import FindEntries

logger = logging.getLogger(__name__)


class PopulateValidateRelease:

    def __init__(self, entry_string='', entry_list=[], entry_file='', keep_logs=False, output_root=None,
                 always_recalculate=False, skip_gzip=False, skip_emdb=False, validation_sub_dir='current',
                 pdb_release=False, emdb_release=False,
                 site_id=getSiteId(), nocache=False,
                 priority=False, subscribe=None):
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
        self.priority_queue = priority
        self.subscribe = subscribe
        if self.priority_queue and self.subscribe:
            logger.critical('error - mixing of priority queues and subscriber queues')
            sys.exit()
        # Get cachedir
        of = outputFiles(siteID=site_id)
        self.__nocache = nocache
        if nocache:
            self.__cache = None
        else:
            self.__cache = of.get_ftp_cache_folder()
        # priority queues
        if self.priority_queue:
            self.make_priorities()


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


    def make_priorities(self):
        fe = FindEntries(siteID=self.site_id)
        # build lists of absolute input file paths and associated entries
        self.modified_priority_paths = fe.get_modified_pdb_paths()
        self.modified_priorities = [os.path.basename(path) for path in self.modified_priority_paths]
        self.added_priority_paths = fe.get_added_pdb_paths()
        self.added_priorities = [os.path.basename(path) for path in self.added_priority_paths]
        self.emdb_priority_paths = fe.get_emdb_paths()
        self.emdb_priorities = [os.path.basename(path) for path in self.emdb_priority_paths]


    def get_priority(self, message):
        # missing - 10
        # new pdb - 8
        # new emdb - 6
        # modified pdb - 4
        # modified emdb - 2
        # default - 1
        priority = 1
        if self.validation_sub_dir and self.validation_sub_dir == 'missing':
            # find_and_run_missing always runs Populate with validation_sub_dir = missing
            priority = 10
        else:
            emd = "emdbID" in message
            pdb = "pdbID" in message
            if not emd and not pdb:
                logger.warning(f"error - neither pdb or emdb {message}")
                return 1
            elif emd and pdb:
                logger.warning(f"error - both pdb and emdb {message}")
                pdb = False
                emd = True
            modified = None
            if self.always_recalculate:
                modified = True
            elif pdb and message["pdbID"] in self.modified_priorities:
                modified = True
            elif pdb and message["pdbID"] in self.added_priorities:
                modified = False
            elif emd and message["emdbID"] in self.emdb_priorities:
                path = None
                for p in self.emdb_priority_paths:
                    if os.path.basename(p) == message["emdbID"]:
                        path = p
                        break
                if path:
                    map_dir = os.path.join(path, "map")
                    if os.path.exists(map_dir):
                        modified = False
                    else:
                        modified = True
            if modified is None:
                logger.warning(f"error - could not get priority for {message}")
                return 1
            if pdb and not modified:
                priority = 8
            elif emd and not modified:
                priority = 6
            elif pdb and modified:
                priority = 4
            elif emd and modified:
                priority = 2
        return priority

    def process_messages(self):
        if self.messages:
            # Set logging for pika to be lower
            plogging = logging.getLogger('pika')
            plogging.setLevel(logging.ERROR)
            for message in self.messages:
                if self.priority_queue:
                    priority = self.get_priority(message)
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
                if self.priority_queue:
                    ok = MessagePublisher().publish(
                        message=json.dumps(message),
                        exchangeName=vc.exchange,
                        queueName=vc.queue_name,
                        routingKey=vc.routing_key,
                        priority=priority
                    )
                elif self.subscribe:
                    ok = MessagePublisher().publishDirect(
                        message=json.dumps(message),
                        exchangeName=self.subscribe,
                    )
                else:
                    ok = MessagePublisher().publish(
                        message=json.dumps(message),
                        exchangeName=vc.exchange,
                        queueName=vc.queue_name,
                        routingKey=vc.routing_key
                    )
                logger.info('MESSAGE {}'.format(ok))
                if not ok:
                    logger.critical('error - could not publish')
                    break

    def test(self):
        if not self.priority_queue:
            logger.info('error - not a priority queue')
            return None
        fape = FindAndProcessEntries(entry_string=self.entry_string,
                                     entry_file=self.entry_file,
                                     entry_list=self.entry_list,
                                     skip_emdb=self.skip_emdb,
                                     pdb_release=self.pdb_release,
                                     emdb_release=self.emdb_release,
                                     site_id=self.site_id,
                                     nocache=self.__nocache)
        fape.find_onedep_entries()
        fape.process_pdb_entries()
        fape.process_emdb_entries()
        if self.emdb_release:
            for emdb_entry in fape.emdb_entries:
                if emdb_entry not in fape.added_entries:
                    message = {"pdbID": emdb_entry}
                    fape.messages.append(message)
                    fape.added_entries.append(emdb_entry)
        self.messages = fape.get_found_entries()
        if self.messages:
            for message in self.messages:
                priority = self.get_priority(message)
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
                logger.info('priority %s msg %s' % (priority, message))
                vc = ValConfig(self.site_id)
                logger.info(f'exchangeName {vc.exchange} queueName {vc.queue_name} routingKey {vc.routing_key}')

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
    parser.add_argument(
        "--test", help="Testing priority values", action="store_true"
    )
    parser.add_argument(
        "--priority", help="Make a priority queue", action='store_true'
    )
    parser.add_argument(
        "--subscribe", help="Exchange name for optional subscriber rather than standard consumer", type=str, default=None
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
                                  nocache=args.nocache,
                                  priority=args.priority,
                                  subscribe=args.subscribe)

    if not args.test:
        pvr.run_process()
    elif args.test:
        logger.info('running unit test')
        pvr.test()


if "__main__" in __name__:
    main()
