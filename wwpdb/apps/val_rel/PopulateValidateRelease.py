import argparse
import json
import logging
import os

from wwpdb.utils.config.ConfigInfo import getSiteId
from wwpdb.utils.message_queue.MessagePublisher import MessagePublisher

from wwpdb.apps.val_rel.config.ValConfig import ValConfig
from wwpdb.apps.val_rel.utils.FindEntries import FindEntries
from wwpdb.apps.val_rel.utils.XmlInfo import XmlInfo
from wwpdb.apps.val_rel.utils.getFilesRelease import getFilesRelease
from wwpdb.apps.val_rel.utils.mmCIFInfo import mmCIFInfo
from wwpdb.apps.val_rel.utils.outputFiles import outputFiles

logger = logging.getLogger(__name__)


class PopulateValidateRelease:

    def __init__(self, entry_string='', entry_list=[], entry_file='', keep_logs=False, output_root=None,
                 always_recalculate=False, skip_gzip=False, skip_emdb=False, validation_sub_dir='current',
                 pdb_release=False, emdb_release=False,
                 site_id=getSiteId()):
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
        self.__cache = of.get_ftp_cache_folder()


    def run_process(self):
        self.find_onedep_entries()
        self.process_entry_file()
        self.process_entry_list()
        self.process_entry_string()
        self.categorise_entries()
        self.process_emdb_entries()
        self.process_pdb_entries()
        self.process_messages()

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
                re = getFilesRelease(siteID=self.site_id, emdb_id=emdb_entry, pdb_id=None, cache=self.__cache)
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

    def process_pdb_entries(self):
        for pdb_entry in self.pdb_entries:
            if pdb_entry not in self.added_entries:
                message = {"pdbID": pdb_entry}
                self.messages.append(message)
                self.added_entries.append(pdb_entry)

    def process_messages(self):
        if self.messages:
            # Set logging for pika to be lower
            plogging = logging.getLogger('pika')
            plogging.setLevel(logging.ERROR)
            for message in self.messages:

                message["siteID"] = self.site_id
                message["keepLog"] = self.keep_logs
                message['subfolder'] = self.validation_sub_dir
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
                                  output_root=args.output_root)

    pvr.run_process()


if "__main__" in __name__:
    main()
