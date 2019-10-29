import argparse
import logging
import os
import glob
import shutil
import json
import sys
from wwpdb.utils.config.ConfigInfo import ConfigInfo, getSiteId
from wwpdb.apps.val_ws_server.validate.ValidateRelease import outputFiles, get_gzip_name
from wwpdb.utils.message_queue.MessagePublisher import MessagePublisher
from wwpdb.apps.val_ws_server.validate.ValidateRelease import queue_name, routing_key, exchange

logger = logging.getLogger()

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
            logging.error('{} missing'.format(get_gzip_name(f)))
            return True
        return False
            
    def find_missing_pdb_entries(self):
        entries = []
        entries.extend(self.get_added_pdb_entries())
        entries.extend(self.get_modifed_pdb_entries())

        logging.info('checking {} entries'.format(len(entries)))

        for entry in entries:
            if entry:
                self.get_pdb_output_folder(pdbid=entry)
                files_to_check_list, file_to_check_dict = self.of.get_core_validation_files()
                for f in files_to_check_list:
                    if self.check_for_missing(f):
                        if entry not in self.entries_missing_files:
                            self.entries_missing_files.append(entry)

        logging.error('{} entries missing files out of {}'.format(len(self.entries_missing_files), len(entries)))
        logging.error(','.join(self.entries_missing_files))

        return self.entries_missing_files

    def find_missing_emdb_entries(self):
        entries = self.get_emdb_entries()

        logging.info('checking {} entries'.format(len(entries)))

        for entry in entries:
            if entry:
                self.get_emdb_output_folder(emdbid=entry)
                files_to_check_list, file_to_check_dict = self.of.get_core_validation_files()
                for f in files_to_check_list:
                    if self.check_for_missing(f):
                        if entry not in self.entries_missing_files:
                            self.entries_missing_files.append(entry)

        logging.error('{} entries missing files out of {}'.format(len(self.entries_missing_files), len(entries)))
        logging.error(','.join(self.entries_missing_files))

        return self.entries_missing_files

    def get_release_entries(self, subfolder):
        entries = list()
        full_entries = glob.glob(os.path.join(self.cI.get('FOR_RELEASE_DATA_PATH'), subfolder) + '/*')
        for full_entry in full_entries:
            if not '.new' in full_entry:
                entry = os.path.basename(full_entry)
                entries.append(entry)
        return entries

    def get_modifed_pdb_entries(self):
        return self.get_release_entries(subfolder='modified')

    def get_added_pdb_entries(self):
        return self.get_release_entries(subfolder='added')

    def get_emdb_entries(self):
        return self.get_release_entries(subfolder='emd')

    def get_pdb_output_folder(self, pdbid):
        self.of.pdbID = pdbid
        return self.of.get_entry_output_folder()
    
    def get_emdb_output_folder(self, emdbid):
        self.of.pdbID = None
        self.of.emdbID = emdbid
        return self.of.get_entry_output_folder()


def main(entry_list=None, entry_file=None, release=False, modified=False, emdb_release=False, missing_pdb=False, missing_emdb=False, 
        siteID=getSiteId(), python_siteID=None, pdb=False, emdb=False, keep_logs=False,output_root=None,
        always_recalculate=False, skipGzip=False):
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
        logging.info('{} entries missing validation information'.format(len(missing_pdbs)))
        logging.info(missing_pdbs)
        pdb_entries.extend(missing_pdbs)
        for entry in fe.find_missing_pdb_entries():
            shutil.rmtree(fe.get_pdb_output_folder(pdbid=entry), ignore_errors=True)

    if missing_emdb:
        missing_emdbs = fe.find_missing_emdb_entries()
        logging.info('{} entries missing validation information'.format(len(missing_emdbs)))
        logging.info(missing_emdbs)
        emdb_entries.extend(missing_emdbs)

    elif entry_list:
        entries.extend(entry_list.split(','))
    elif entry_file:
        if os.path.exists(entry_file):
            with open(entry_file) as inFile:
                for l in inFile:
                    entries.append(l.strip())
        else:
            logging.error('file: %s not found' % entry_file)
    
    if entries and pdb:
        pdb_entries.extend(entries)
    elif entries and emdb:
        emdb_entries.extend(entries)
    else:
        logging.error('entries given but not specified if pdb or emdb IDs')

    added_entries = []

    for pdb_entry in pdb_entries:
        if pdb_entry not in added_entries:
            message = {'pdbID': pdb_entry}
            
            messages.append(message)
            added_entries.append(pdb_entry)

    for emdb_entry in emdb_entries:
        if emdb_entry not in added_entries:
            message = {'emdbID': emdb_entry}
            messages.append(message)
            added_entries.append(emdb_entry)

    if messages:
        for message in messages:
            message['siteID'] = siteID
            message['keepLog'] = keep_logs
            if python_siteID:
                message['python_site_id'] = python_siteID
            if output_root:
                message['outputRoot'] = output_root
            if always_recalculate:
                message['alwaysRecalculate'] = always_recalculate
            if skipGzip:
                message['skipGzip'] = skipGzip
            MessagePublisher().publish(message=json.dumps(message), exchangeName=exchange, queueName=queue_name, routingKey=routing_key)
    

if '__main__' in __name__:
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', help='debugging', action='store_const', dest='loglevel',
                        const=logging.DEBUG,
                        default=logging.INFO)
    parser.add_argument('--entry_list', help='comma separated list of entries', type=str)
    parser.add_argument('--entry_file', help='file containing list of entries - one per line', type=str)
    parser.add_argument('--emdb', help='entries are EMDB', action='store_true')
    parser.add_argument('--pdb', help='entries are PDB', action='store_true')
    parser.add_argument('--release', help='run entries scheduled for new release', action='store_true')
    parser.add_argument('--modified', help='run entries scheduled for modified release', action='store_true')
    parser.add_argument('--emdb_release', help='run entries scheduled for emdb release', action='store_true')
    parser.add_argument('--find_missing_pdb', help='find PDB entries missing validation reports', action='store_true')
    parser.add_argument('--find_missing_emdb', help='find EMDB entries missing validation reports', action='store_true')
    parser.add_argument('--keep_logs', help='Keep the log files', action='store_true')
    parser.add_argument('--always_recalculate', help='always recalculate', action='store_true')
    parser.add_argument('--skipGzip', help='skip gizpping output files', action='store_true')
    parser.add_argument('--siteID', help='siteID', type=str, default=getSiteId())
    parser.add_argument('--python_siteID', help='siteID for the OneDep code', type=str)
    parser.add_argument('--output_root', help='folder to output the results to - overwrides default onedep folder', type=str)
    args = parser.parse_args()
    logger.setLevel(args.loglevel)

    if (args.entry_list or args.entry_file) and not (args.emdb or args.pdb):
        print('please specify if entries are --pdb or --emdb')
        sys.exit(1)

    main(entry_list=args.entry_list, entry_file=args.entry_file,
         modified=args.modified, release=args.release, emdb_release=args.emdb_release, missing_pdb=args.find_missing_pdb, missing_emdb=args.find_missing_emdb, 
         siteID=args.siteID, pdb=args.pdb, emdb=args.emdb, python_siteID=args.python_siteID,
         keep_logs=args.keep_logs, always_recalculate=args.always_recalculate, skipGzip=args.skipGzip)

    