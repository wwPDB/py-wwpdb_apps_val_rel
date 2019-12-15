import argparse
import logging
import os
import glob
import shutil
import json
import sys


# Create logger - 
FORMAT = '[%(asctime)s %(levelname)s]-%(module)s.%(funcName)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


from wwpdb.utils.config.ConfigInfo import ConfigInfo, getSiteId
from wwpdb.utils.message_queue.MessagePublisher import MessagePublisher
from wwpdb.apps.val_rel.outputFiles import outputFiles
from wwpdb.apps.val_rel.ValidateRelease import (
    queue_name,
    routing_key,
    exchange,
    get_gzip_name,
)
from wwpdb.apps.val_rel.getFilesRelease import getFilesRelease
from wwpdb.apps.val_rel.xml_data import xmlInfo
from wwpdb.apps.val_rel.mmCIFInfo import mmCIFInfo
from wwpdb.io.locator.ReleasePathInfo import ReleasePathInfo

class FindEntries:
    def __init__(self, siteID=getSiteId()):
        self.siteID = siteID
        self.of = outputFiles(siteID=self.siteID)
        self.cI = ConfigInfo(self.siteID)
        self.entries_missing_files = []
        self.missing_files = []

    def check_for_missing(self, f):
        if not os.path.exists(get_gzip_name(f)):
            self.missing_files.append(get_gzip_name(f))
            logger.error("{} missing".format(get_gzip_name(f)))
            return True
        return False

    def find_missing_pdb_entries(self):
        entries = []
        entries.extend(self.get_added_pdb_entries())
        entries.extend(self.get_modifed_pdb_entries())

        logger.info("checking {} entries".format(len(entries)))

        for entry in entries:
            if entry:
                self.get_pdb_output_folder(pdbid=entry)
                file_to_check_dict = self.of.get_core_validation_files()
                for f in file_to_check_dict.values():
                    if self.check_for_missing(f):
                        if entry not in self.entries_missing_files:
                            self.entries_missing_files.append(entry)

        logger.error(
            "{} entries missing files out of {}".format(
                len(self.entries_missing_files), len(entries)
            )
        )
        logger.error(",".join(self.entries_missing_files))

        return self.entries_missing_files

    def find_missing_emdb_entries(self):
        entries = self.get_emdb_entries()

        logger.info("checking {} entries".format(len(entries)))

        for entry in entries:
            if entry:
                self.get_emdb_output_folder(emdbid=entry)
                file_to_check_dict = self.of.get_core_validation_files()
                for f in file_to_check_dict.values():
                    if self.check_for_missing(f):
                        if entry not in self.entries_missing_files:
                            self.entries_missing_files.append(entry)

        logger.error(
            "{} entries missing files out of {}".format(
                len(self.entries_missing_files), len(entries)
            )
        )
        logger.error(",".join(self.entries_missing_files))

        return self.entries_missing_files

    def get_release_entries(self, subfolder):
        entries = list()
        rpi = ReleasePathInfo(self.siteID)
        full_entries = glob.glob(
            os.path.join(rpi.getForReleasePath(subdir=subfolder), "*")
        )
        for full_entry in full_entries:
            if not ".new" in full_entry:
                entry = os.path.basename(full_entry)
                entries.append(entry)
        return entries

    def get_modifed_pdb_entries(self):
        return self.get_release_entries(subfolder="modified")

    def get_added_pdb_entries(self):
        return self.get_release_entries(subfolder="added")

    def get_emdb_entries(self):
        return self.get_release_entries(subfolder="emd")

    def get_pdb_output_folder(self, pdbid):
        self.of.pdbID = pdbid
        return self.of.get_entry_output_folder()

    def get_emdb_output_folder(self, emdbid):
        self.of.pdbID = None
        self.of.emdbID = emdbid
        return self.of.get_entry_output_folder()


def main(
    entry_list=None,
    entry_file=None,
    release=False,
    modified=False,
    emdb_release=False,
    missing_pdb=False,
    missing_emdb=False,
    siteID=getSiteId(),
    python_siteID=None,
    keep_logs=False,
    output_root=None,
    always_recalculate=False,
    skipGzip=False,
    validation_sub_dir='current'
):
    pdb_entries = []
    emdb_entries = []
    entries = []
    messages = []

    fe = FindEntries(siteID=siteID)

    if release:
        pdb_entries.extend(fe.get_added_pdb_entries())
    if modified:
        pdb_entries.extend(fe.get_modifed_pdb_entries())

    if emdb_release:
        emdb_entries.extend(fe.get_emdb_entries())

    if missing_pdb:
        missing_pdbs = fe.find_missing_pdb_entries()
        logger.info(
            "{} entries missing validation information".format(len(missing_pdbs))
        )
        logger.info(missing_pdbs)
        pdb_entries.extend(missing_pdbs)
        for entry in fe.find_missing_pdb_entries():
            shutil.rmtree(fe.get_pdb_output_folder(pdbid=entry), ignore_errors=True)

    if missing_emdb:
        missing_emdbs = fe.find_missing_emdb_entries()
        logger.info(
            "{} entries missing validation information".format(len(missing_emdbs))
        )
        logger.info(missing_emdbs)
        emdb_entries.extend(missing_emdbs)

    elif entry_list:
        entries.extend(entry_list.split(","))
    elif entry_file:
        if os.path.exists(entry_file):
            with open(entry_file) as inFile:
                for l in inFile:
                    entries.append(l.strip())
        else:
            logger.error("file: %s not found" % entry_file)

    for entry in entries:
        if "EMD-" in entry.upper():
            emdb_entries.append(entry)
        else:
            pdb_entries.append(entry)

    added_entries = []

    for emdb_entry in emdb_entries:
        if emdb_entry not in added_entries:
            # stop duplication of making EM validation reports twice
            logger.debug(emdb_entry)
            re = getFilesRelease(siteID=siteID)
            em_xml = re.get_emdb_xml(emdb_entry)
            
            em_vol = re.get_emdb_volume(emdb_entry)
            if em_vol:
                logger.debug('using XML: {}'.format(em_xml))
                pdbids = xmlInfo(em_xml).get_pdbids_from_xml() 
                if pdbids:
                    logger.info(
                        "PDB entries associated with {}: {}".format(emdb_entry, ",".join(pdbids))
                    )
                    for pdbid in pdbids:
                        pdbid = pdbid.lower()
                        pdb_file = re.get_model(pdbid)
                        if pdb_file:
                            cf = mmCIFInfo(pdb_file)
                            associated_emdb = cf.get_associated_emdb()
                            if associated_emdb == emdb_entry:
                                if pdbid in pdb_entries:
                                    logger.info(
                                        "removing {} from the PDB queue to stop duplication of report generation".format(
                                            pdbid
                                        )
                                    )
                                    pdb_entries.remove(pdbid)
                            # what if its not? should it be added to the queue?
                        else:
                            if pdbid in pdb_entries:
                                logger.info('removing {} as pdb file does not exist'.format(pdbid))
                                pdb_entries.remove(pdbid)

                message = {"emdbID": emdb_entry}
                messages.append(message)
                added_entries.append(emdb_entry)

    for pdb_entry in pdb_entries:
        if pdb_entry not in added_entries:
            message = {"pdbID": pdb_entry}
            messages.append(message)
            added_entries.append(pdb_entry)

    if messages:
        for message in messages:
            logger.info('MESSAGE req %s' % message) 
            message["siteID"] = siteID
            message["keepLog"] = keep_logs
            message['subfolder'] = validation_sub_dir
            if python_siteID:
                message["python_site_id"] = python_siteID
            if output_root:
                message["outputRoot"] = output_root
            if always_recalculate:
                message["alwaysRecalculate"] = always_recalculate
            if skipGzip:
                message["skipGzip"] = skipGzip
            MessagePublisher().publish(
                message=json.dumps(message),
                exchangeName=exchange,
                queueName=queue_name,
                routingKey=routing_key,
            )


if "__main__" in __name__:
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
        "--release", help="run entries scheduled for new release", action="store_true"
    )
    parser.add_argument(
        "--modified",
        help="run entries scheduled for modified release",
        action="store_true",
    )
    parser.add_argument(
        "--emdb_release",
        help="run entries scheduled for emdb release",
        action="store_true",
    )
    parser.add_argument(
        "--find_missing_pdb",
        help="find PDB entries missing validation reports",
        action="store_true",
    )
    parser.add_argument(
        "--find_missing_emdb",
        help="find EMDB entries missing validation reports",
        action="store_true",
    )
    parser.add_argument("--keep_logs", help="Keep the log files", action="store_true")
    parser.add_argument(
        "--always_recalculate", help="always recalculate", action="store_true"
    )
    parser.add_argument(
        "--skipGzip", help="skip gizpping output files", action="store_true"
    )
    parser.add_argument("--siteID", help="siteID", type=str, default=getSiteId())
    parser.add_argument("--python_siteID", help="siteID for the OneDep code", type=str)
    parser.add_argument("--validation_subdir", help="validation sub directory", type=str, default='current')
    parser.add_argument(
        "--output_root",
        help="folder to output the results to - overwrides default OneDep folder",
        type=str,
    )
    args = parser.parse_args()
    logger.setLevel(args.loglevel)

    # Set logging for pika to be lower
    plogging = logging.getLogger('pika')
    plogging.setLevel(logging.ERROR)

    main(
        entry_list=args.entry_list,
        entry_file=args.entry_file,
        modified=args.modified,
        release=args.release,
        emdb_release=args.emdb_release,
        missing_pdb=args.find_missing_pdb,
        missing_emdb=args.find_missing_emdb,
        siteID=args.siteID,
        python_siteID=args.python_siteID,
        keep_logs=args.keep_logs,
        always_recalculate=args.always_recalculate,
        skipGzip=args.skipGzip,
        validation_sub_dir=args.validation_subdir
    )

