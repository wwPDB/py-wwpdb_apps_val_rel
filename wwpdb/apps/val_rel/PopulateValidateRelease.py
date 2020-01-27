import argparse
import logging
import os
import glob
import shutil
import json

from wwpdb.utils.config.ConfigInfo import ConfigInfo, getSiteId
from wwpdb.utils.message_queue.MessagePublisher import MessagePublisher
from wwpdb.apps.val_rel.config.ValConfig import ValConfig
from wwpdb.apps.val_rel.utils.getFilesRelease import getFilesRelease
from wwpdb.apps.val_rel.utils.XmlInfo import XmlInfo
from wwpdb.apps.val_rel.utils.mmCIFInfo import mmCIFInfo
from wwpdb.io.locator.ReleasePathInfo import ReleasePathInfo

# Create logger -
FORMAT = '[%(asctime)s %(levelname)s]-%(module)s.%(funcName)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


class FindEntries:
    def __init__(self, siteID=getSiteId()):
        self.siteID = siteID
        self.cI = ConfigInfo(self.siteID)
        self.entries_missing_files = []
        self.missing_files = []

    def _get_release_entries(self, subfolder):
        """Returns list of entries in for_release/subfolder directory.
        Ignores directories that end in ".new" being created by release module.
        """
        entries = list()
        rpi = ReleasePathInfo(self.siteID)
        dirpath = rpi.getForReleasePath(subdir=subfolder)
        full_entries = glob.glob(os.path.join(dirpath, "*"))
        for full_entry in full_entries:
            if ".new" not in full_entry:
                # Ensure not some other random file
                if os.path.isdir(full_entry):
                    entry = os.path.basename(full_entry)
                    entries.append(entry)
        return entries

    def get_modified_pdb_entries(self):
        """Returns list of entries in the for_release/modified directory"""
        return self._get_release_entries(subfolder="modified")

    def get_added_pdb_entries(self):
        """Return list of entries in the for_release/added directory"""
        return self._get_release_entries(subfolder="added")

    def get_emdb_entries(self):
        """Return list of entries in the for_release/emd directory"""
        return self._get_release_entries(subfolder="emd")


def main(
    entry_list=None,
    entry_file=None,
    release=False,
    modified=False,
    emdb_release=False,
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
        pdb_entries.extend(fe.get_modified_pdb_entries())

    if emdb_release:
        emdb_entries.extend(fe.get_emdb_entries())

    if entry_list:
        entries.extend(entry_list.split(","))
    elif entry_file:
        if os.path.exists(entry_file):
            with open(entry_file) as inFile:
                for l in inFile:
                    entries.append(l.strip())
        else:
            logger.error("file: %s not found", entry_file)

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
                logger.debug('using XML: %s', em_xml)
                pdbids = XmlInfo(em_xml).get_pdbids_from_xml()
                if pdbids:
                    logger.info(
                        "PDB entries associated with %s: %s", emdb_entry, ",".join(pdbids)
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
                                        "removing %s from the PDB queue to stop duplication of report generation",
                                        pdbid
                                    )
                                    pdb_entries.remove(pdbid)
                            # what if its not? should it be added to the queue?
                        else:
                            if pdbid in pdb_entries:
                                logger.info('removing %s as pdb file does not exist', pdbid)
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
            logger.info('MESSAGE req %s', message)
            vc = ValConfig(siteID)
            ok = MessagePublisher().publish(
                message=json.dumps(message),
                exchangeName=vc.exchange,
                queueName=vc.queue_name,
                routingKey=vc.routing_key,
                )
            logger.info('MESSAGE {}'.format(ok))


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
        siteID=args.siteID,
        python_siteID=args.python_siteID,
        keep_logs=args.keep_logs,
        always_recalculate=args.always_recalculate,
        skipGzip=args.skipGzip,
        validation_sub_dir=args.validation_subdir
    )
