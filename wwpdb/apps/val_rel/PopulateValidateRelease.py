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

# Create logger -
FORMAT = '[%(asctime)s %(levelname)s]-%(module)s.%(funcName)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def remove_unwanted_folders(pdb_entries):
    pdb_val_report_dir = outputFiles().get_pdb_root_folder()
    val_pdbids = set()
    if os.path.exists(pdb_val_report_dir):
        for pdbid in [d for d in os.listdir(pdb_val_report_dir) if os.path.isdir(d)]:
            if pdbid not in pdb_entries:
                full_dir = os.path.join(pdb_val_report_dir, pdbid)
                logging.error('will remove {}'.format(full_dir))
                # shutil.rmtree(full_dir)


def main(
        entry_list=None,
        entry_file=None,
        pdb_release=False,
        emdb_release=False,
        siteID=getSiteId(),
        python_siteID=None,
        keep_logs=False,
        output_root=None,
        always_recalculate=False,
        skipGzip=False,
        skip_emdb=False,
        validation_sub_dir='current'
):
    all_pdb_entries = set()
    pdb_entries = []
    emdb_entries = []
    entries = []
    messages = []

    fe = FindEntries(siteID=siteID)

    if pdb_release:
        pdb_entries.extend(fe.get_added_pdb_entries())
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
    for pdbid in pdb_entries:
        all_pdb_entries.add(pdbid)

    for emdb_entry in emdb_entries:
        if emdb_entry not in added_entries:
            # stop duplication of making EM validation reports twice
            logger.debug(emdb_entry)
            re = getFilesRelease(siteID=siteID, emdb_id=emdb_entry, pdb_id=None)
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
                                if pdbid in pdb_entries:
                                    logger.info(
                                        "removing %s from the PDB queue to stop duplication of report generation",
                                        pdbid
                                    )
                                    pdb_entries.remove(pdbid)
                                else:
                                    all_pdb_entries.add(pdbid)
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
            if skip_emdb:
                message['skip_emdb'] = skip_emdb
            logger.info('MESSAGE req %s', message)
            vc = ValConfig(siteID)
            ok = MessagePublisher().publish(
                message=json.dumps(message),
                exchangeName=vc.exchange,
                queueName=vc.queue_name,
                routingKey=vc.routing_key,
            )
            logger.info('MESSAGE {}'.format(ok))

    if pdb_release:
        remove_unwanted_folders(pdb_entries=all_pdb_entries)


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

    # Set logging for pika to be lower
    plogging = logging.getLogger('pika')
    plogging.setLevel(logging.ERROR)

    main(
        entry_list=args.entry_list,
        entry_file=args.entry_file,
        pdb_release=args.pdb_release,
        emdb_release=args.emdb_release,
        siteID=args.siteID,
        python_siteID=args.python_siteID,
        keep_logs=args.keep_logs,
        always_recalculate=args.always_recalculate,
        skipGzip=args.skipGzip,
        skip_emdb=args.skip_emdb,
        validation_sub_dir=args.validation_subdir,
        output_root=args.output_root
    )
