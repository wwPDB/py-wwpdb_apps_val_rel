import argparse
import json
import logging
import re
import os
import sys

from wwpdb.apps.val_rel.config.ValConfig import ValConfig
from wwpdb.utils.config.ConfigInfo import getSiteId
from wwpdb.apps.val_rel.utils.outputFiles import outputFiles
from wwpdb.utils.message_queue.MessagePublisher import MessagePublisher
from wwpdb.apps.val_rel.utils.FindAndProcessEntries import FindAndProcessEntries
from wwpdb.apps.val_rel.utils.FindEntries import FindEntries
from wwpdb.apps.val_rel.utils.checkModifications import already_run

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
        # Get cachedir
        of = outputFiles(siteID=site_id)
        self.__nocache = nocache
        if nocache:
            self.__cache = None
        else:
            self.__cache = of.get_ftp_cache_folder()
        if self.priority_queue and (not self.validation_sub_dir or self.validation_sub_dir != 'missing'):
            # help find priorities
            fe = FindEntries(siteID=self.site_id)
            # absolute folder paths
            paths = fe.get_modified_pdb_paths()
            # fape does not run validation on the added folder
            # paths.extend(fe.get_added_pdb_paths())
            paths.extend(fe.get_emdb_paths())
            self.unmodifieds = {}
            for source_path in paths:
                # folder names
                key = os.path.basename(source_path)
                output_path = None
                if key.startswith('EMD'):
                    of.set_emdb_id(key)
                    output_path = of.get_emdb_output_folder()
                elif re.match(r'^\d{1}\w{3}$', key):
                    of.set_pdb_id(key)
                    output_path = of.get_pdb_output_folder()
                if output_path:
                    self.unmodifieds[key] = already_run(source_path, output_path)
                else:
                    logger.info('error - no output path for %s', key)

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

    def get_priority(self, message):
        """priority
        missing - 10
        new pdb - 8
        new emdb - 6
        modified pdb - 4
        modified emdb - 2
        default - 1
        """
        priority = 1
        if self.validation_sub_dir and self.validation_sub_dir == 'missing':
            # find_and_run_missing always runs Populate with validation_sub_dir = missing
            priority = 10
        else:
            # already run = new
            # not already run = modified
            # always_recalculate = modified
            mod = False
            if self.always_recalculate:
                mod = True
            elif message["pdbID"] and message["pdbID"] in self.unmodifieds:
                mod = not self.unmodifieds[message["pdbID"]]
            emd = (self.validation_sub_dir and self.validation_sub_dir == 'emd') or (message["pdbID"] and message["pdbID"].startswith("EMD"))
            pdb = not emd
            if pdb and not mod:
                priority = 8
            elif emd and not mod:
                priority = 6
            elif pdb and mod:
                priority = 4
            elif emd and mod:
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
                    if not self.subscribe:
                        ok = MessagePublisher().publish(
                            message=json.dumps(message),
                            exchangeName=vc.exchange,
                            queueName=vc.queue_name,
                            routingKey=vc.routing_key,
                            priority=priority
                        )
                    else:
                        ok = MessagePublisher().publishDirect(
                            message=json.dumps(message),
                            exchangeName=self.subscribe,
                            priority=priority
                        )
                else:
                    if not self.subscribe:
                        ok = MessagePublisher().publish(
                            message=json.dumps(message),
                            exchangeName=vc.exchange,
                            queueName=vc.queue_name,
                            routingKey=vc.routing_key
                        )
                    else:
                        ok = MessagePublisher().publishDirect(
                            message=json.dumps(message),
                            exchangeName=self.subscribe,
                        )
                logger.info('MESSAGE {}'.format(ok))

    def test(self):
        if not self.priority_queue:
            print('error - not a priority queue')
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
        # fape.process_emdb_entries()
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
                print('priority %s msg %s' % (priority, message))
                vc = ValConfig(self.site_id)
                print(f'exchangeName {vc.exchange} queueName {vc.queue_name} routingKey {vc.routing_key}')

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
        print('running unit test')
        pvr.test()


if "__main__" in __name__:
    main()
