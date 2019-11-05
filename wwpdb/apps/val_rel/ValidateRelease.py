import logging
import shutil
import tempfile
import gzip
import os
import sys
import argparse
import xml.etree.ElementTree as ET
import logging
from wwpdb.utils.config.ConfigInfo import ConfigInfo, getSiteId
from wwpdb.utils.dp.ValidationWrapper import ValidationWrapper

from wwpdb.apps.validation.src.utils.minimal_map_cif import GenerateMinimalCif

from wwpdb.apps.val_rel.outputFiles import outputFiles
from wwpdb.apps.val_rel.getFilesRelease import getFilesRelease
from wwpdb.apps.val_rel.mmCIFInfo import mmCIFInfo

logger = logging.getLogger()
FORMAT = "%(funcName)s (%(levelname)s) - %(message)s"
logging.basicConfig(format=FORMAT)

queue_name = "val_release_queue"
routing_key = "val_release_requests"
exchange = "val_release_exchange"


def get_pdbids_from_xml(xml_file):
    pdbids = []
    tree = ET.parse(xml_file)
    root = tree.getroot()
    if list(root.iter("pdb_id")):
        for pdbid in root.iter("pdb_id"):
            pdbids.append(pdbid.text)
        logging.info(pdbids)
        return pdbids
    else:
        return []


def already_run(test_file, output_folder):
    if test_file:
        if os.path.exists(test_file):
            if os.path.exists(output_folder):
                input_modification_time = os.path.getmtime(test_file)
                output_modification_time = os.path.getmtime(output_folder)
                if input_modification_time < output_modification_time:
                    logging.info("already run validation")
                    return True
                else:
                    logging.info("validation to be run")
                    return False
            else:
                logging.info("validation to be run")
                return False
        else:
            logging.info('missing input file - not running')
            return True
    else:
        logging.info('missing input file - not running')
        return True


def get_gzip_name(f):
    return f + ".gz"


def gzip_file(inFile):
    if os.path.exists(inFile):
        with open(inFile) as f_in, gzip.open(get_gzip_name(inFile), "wb") as f_out:
            f_out.writelines(f_in)
        os.unlink(inFile)


def remove_files(file_list):
    if file_list:
        logging.debug('removing existing files')
        logging.debug(file_list)
        for f in file_list:
            if os.path.exists(f):
                os.remove(f)
            gzip_f = get_gzip_name(f)
            if os.path.exists(gzip_f):
                os.remove(gzip_f)


class runValidation:
    def __init__(self):
        self.keepLog = False
        self.pdbid = None
        self.emdbid = None
        self.emdbids = []
        self.pdbids = []
        self.siteID = None
        self.outputRoot = None
        self.entry_id = None
        self.modelPath = None
        self.csPath = None
        self.sfPath = None
        self.emXmlPath = None
        self.volPath = None
        self.fscPath = None
        self.tempDir = None
        self.session_path = None
        self.runDir = None
        # self.contour_level = None # not needed as its in the xml
        self.entry_output_folder = None
        self.pdb_output_folder = None
        self.emdb_output_folder = None
        self.output_file_list = []
        self.output_file_dict = {}

        self.skip_gzip = False
        self.always_recalculate = False

        self.copy_to_root_emdb = False

        self.rel_files = None

    def check_pdb_already_run(self):
        if self.always_recalculate:
            return True
        modified = False
        if not already_run(self.modelPath, self.pdb_output_folder):
            modified = True
        if self.sfPath:
            if not already_run(self.sfPath, self.pdb_output_folder):
                modified = True
        if self.csPath:
            if not already_run(self.csPath, self.pdb_output_folder):
                modified = True
        return modified

    def check_emdb_already_run(self):
        if self.always_recalculate:
            return True
        modified = False
        if not already_run(self.emXmlPath, self.emdb_output_folder):
            modified = True
        return modified

    def check_modified(self):
        self.set_output_dir_and_files()
        pdb_modified = self.check_pdb_already_run()
        emdb_modified = self.check_emdb_already_run()

        if pdb_modified or emdb_modified:
            return True
        return False

    def set_output_dir_and_files(self):
        of = outputFiles(
                pdbID=self.pdbid,
                emdbID=self.emdbid,
                siteID=self.siteID,
                outputRoot=self.outputRoot,
            )   
        self.entry_output_folder = of.get_entry_output_folder()
        logging.info('output folder: {}'.format(self.entry_output_folder))
        self.output_file_dict = of.get_all_validation_files()
        self.pdb_output_folder = of.get_pdb_output_folder()
        self.emdb_output_folder = of.get_emdb_output_folder()

    def run_process(self, message):
        self.pdbid = message.get("pdbID")
        if self.pdbid:
            self.pdbid = self.pdbid.lower()
        self.emdbid = message.get("emdbID")
        if self.emdbid:
            self.emdbid = self.emdbid.upper()
        self.siteID = message.get("siteID")
        self.outputRoot = message.get("outputRoot")
        self.skip_gzip = message.get("skipGzip", False)
        self.always_recalculate = message.get("alwaysRecalculate", False)
        self.keepLog = message.get("keepLog", False)
        if self.pdbid:
            self.entry_id = self.pdbid
        elif self.emdbid:
            self.entry_id = self.emdbid
        else:
            logging.error('No PDB or EMDB provided')
            return False
        if not self.siteID:
            self.siteID = getSiteId()
        self.pythonSiteID = message.get("python_site_id", self.siteID)
        self.cI = ConfigInfo(self.siteID)
        self.entry_output_folder = None

        logging.info("running validation for {}, {}".format(self.pdbid, self.emdbid))

        self.rel_files = getFilesRelease(siteID=self.siteID)

        worked = False
        self.session_path = self.cI.get("SITE_WEB_APPS_SESSIONS_PATH")
        self.tempDir = tempfile.mkdtemp(
            dir=self.session_path,
            prefix="{}_validation_release_temp_".format(self.entry_id),
        )

        if self.pdbid:
            self.modelPath = self.rel_files.get_model(self.pdbid)
            self.sfPath = self.rel_files.get_sf(self.pdbid)
            self.csPath = self.rel_files.get_cs(self.pdbid)
            

            cf = mmCIFInfo(self.modelPath)
            exp_methods = cf.get_exp_methods()
            if "ELECTRON MICROSCOPY" in exp_methods:
                # self.contour_level = cf.get_em_map_contour_level() # not needed as its in the XML
                if not self.emdbid:
                    self.emdbid = cf.get_associated_emdb()
                    self.copy_to_root_emdb = True

            return self.run_validation()

        elif self.emdbid:
            self.emXmlPath = self.rel_files.get_emdb_xml(self.emdbid)
            
            self.pdbids = get_pdbids_from_xml(self.emXmlPath)

            if self.pdbids:
                for position, self.pdbid in enumerate(self.pdbids):
                    self.pdbid = self.pdbid.lower()
                    if position == 0:
                        self.copy_to_root_emdb = True
                    else:
                        self.copy_to_root_emdb = False
                    all_worked = []
                    self.modelPath = self.rel_files.get_model(self.pdbid)
                    worked = self.run_validation()
                    all_worked.append(worked)
                if list(set(all_worked)) == [True]:
                    return True
                else:
                    logging.error(self.pdbids)
                    logging.error(all_worked)
                    return False

            else:
                self.modelPath = os.path.join(
                    self.tempDir, "{}_minimal.cif".format(self.emdbid)
                )
                GenerateMinimalCif(emdb_xml=self.emXmlPath).write_out(
                    output_cif=self.modelPath
                )
                # run validation
                return self.run_validation()

    def copy_to_emdb(self, copy_to_root_emdb=False):
        if self.emdbid:
            of = outputFiles(
                pdbID=self.pdbid,
                emdbID=self.emdbid,
                siteID=self.siteID,
                outputRoot=self.outputRoot,
            ) 
            logging.info("EMDB ID: {}".format(self.emdbid))
            emdb_output_folder = of.get_emdb_output_folder()
            if emdb_output_folder != self.entry_output_folder:
                if os.path.exists(emdb_output_folder):
                    logging.info("EMDB output folder: {}".format(emdb_output_folder))
                    of.set_accession_variables(with_emdb=True, copy_to_root_emdb=copy_to_root_emdb)
                    emdb_output_file_dict = of.get_core_validation_files()                    
                    logging.info(
                        "EMDB output file dict: {}".format(emdb_output_file_dict)
                    )
                    for k in self.output_file_dict:
                        if k in emdb_output_file_dict:
                            inFile = self.output_file_dict[k]
                            if os.path.exists(inFile):
                                shutil.copy(
                                    self.output_file_dict[k], emdb_output_file_dict[k]
                                )
                    for f in emdb_output_file_dict.values():
                        gzip_file(f)
                else:
                    logging.error(
                        "EMDB output folder {} does not exist".format(
                            emdb_output_folder
                        )
                    )
                    return False

        return True

    def gzip_output(self):
        for f in self.output_file_list:
            gzip_file(f)

    def run_validation(self):
        try:
            if self.emdbid:
                if not self.emXmlPath:
                    self.emXmlPath = self.rel_files.get_emdb_xml(self.emdbid)
                self.volPath = self.rel_files.get_emdb_volume(self.emdbid)
                self.fscPath = self.rel_files.get_emdb_fsc(self.emdbid)
            if self.pdbid:
                self.sfPath = self.rel_files.get_sf(self.pdbid)
                self.csPath = self.rel_files.get_cs(self.pdbid)

            # check if any input files have changed and set output folders
            is_modified = self.check_modified()
            if not is_modified:
                logging.info("skipping {}/{} as entry files have not changed".format(self.pdbid, self.emdbid))
                return True

            # make output directory if it doesn't exist
            if not os.path.exists(self.entry_output_folder):
                os.makedirs(self.entry_output_folder)
            else:
                os.utime(self.entry_output_folder)
                
            logging.info("Entry output folder: {}".format(self.entry_output_folder))
            self.logPath = os.path.join(self.entry_output_folder, "validation.log")

            # clearing existing reports before making new ones
            self.output_file_list = []
            for key in ['pdf', 'xml', 'full_pdf', 'png', 'svg', '2fofc', 'fofc']:
                if key in self.output_file_dict:
                    self.output_file_list.append(self.output_file_dict[key])

            remove_files(self.output_file_list)

            if self.emdbid:
                em_of = outputFiles(
                    pdbID=self.pdbid,
                    emdbID=self.emdbid,
                    siteID=self.siteID,
                    outputRoot=self.outputRoot,
                    )
                # make emdb output folder if it doesn't exist
                emdb_output_folder = em_of.get_emdb_output_folder()
                if emdb_output_folder != self.entry_output_folder:
                    if not os.path.exists(emdb_output_folder):
                        os.makedirs(emdb_output_folder)
                em_of.set_accession_variables(with_emdb=True)
                emdb_output_file_dict = em_of.get_core_validation_files()
                remove_files(emdb_output_file_dict.values())
                if self.copy_to_root_emdb:
                    em_of.set_accession_variables(with_emdb=True, copy_to_root_emdb=self.copy_to_root_emdb)
                    emdb_output_file_dict = em_of.get_core_validation_files()
                    remove_files(emdb_output_file_dict.values())

            self.runDir = tempfile.mkdtemp(
                dir=self.session_path,
                prefix="{}_validation_release_rundir_".format(self.entry_id),
            )

            logging.info("input files")
            logging.info("model: {}".format(self.modelPath))
            logging.info("SF: {}".format(self.sfPath))
            logging.info("cs: {}".format(self.csPath))
            logging.info("EM volume: {}".format(self.volPath))
            logging.info("EM XML: {}".format(self.emXmlPath))
            logging.info("entry_id: {}".format(self.entry_id))
            logging.info("pdb_id: {}".format(self.pdbid))
            logging.info("emdb_id: {}".format(self.emdbid))

            vw = ValidationWrapper(
                tmpPath=self.tempDir,
                siteId=self.pythonSiteID,
                verbose=False,
                log=sys.stderr,
            )
            vw.imp(self.modelPath)
            vw.addInput(name="run_dir", value=self.runDir)
            vw.addInput(name="request_validation_mode", value="release")
            if self.pdbid:
                vw.addInput(name="entry_id", value=self.pdbid)
            elif self.emdbid:
                vw.addInput(name="entry_id", value=self.emdbid)
                vw.addInput(name="emdb_id", value=self.emdbid)

            if self.sfPath is not None and os.access(self.sfPath, os.R_OK):
                vw.addInput(name="sf_file_path", value=self.sfPath)

            if self.csPath is not None and os.access(self.csPath, os.R_OK):
                vw.addInput(name="cs_file_path", value=self.csPath)

            if self.volPath is not None and os.access(self.volPath, os.R_OK):
                vw.addInput(name="vol_file_path", value=self.volPath)

            if self.emXmlPath is not None and os.access(self.emXmlPath, os.R_OK):
                vw.addInput(name="emdb_xml_path", value=self.emXmlPath)

            if self.fscPath is not None and os.access(self.fscPath, os.R_OK):
                vw.addInput(name="fsc_file_path", value=self.fscPath)

            vw.op("annot-wwpdb-validate-all-sf")
            # output log file
            if self.keepLog:
                vw.expLog(self.logPath)

            logging.info(self.output_file_list)
            logging.info(self.output_file_dict)
            vw.expList(dstPathList=self.output_file_list)

            # clean up temp folder after run
            # vw.cleanup()

            if self.pdbid and self.emdbid:
                ok = self.copy_to_emdb()
                if not ok:
                    logging.error('failed to copy to emdb folder')
                    return False
                if self.copy_to_root_emdb:
                    logging.info('copy to EMDB folder without PDBID')
                    ok = self.copy_to_emdb(self.copy_to_root_emdb)
                    if not ok:
                        logging.error('failed to copy to emdb folder as root')
                        return False
            
            if not self.skip_gzip:
                self.gzip_output()

            return True
        except Exception as e:
            logging.error(e)
            return False


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
    parser.add_argument("--pdbid", help="pdb_id to run on", type=str)
    parser.add_argument("--emdbid", help="emdb_id to run on", type=str)
    parser.add_argument("--output_root", help="root folder to output to", type=str)
    parser.add_argument("--site_id", help="site id to get files from", type=str)
    parser.add_argument(
        "--python_site_id", help="site id to get python code from", type=str
    )
    parser.add_argument(
        "--skip_gzip", help="skip gzipping of files", action="store_true"
    )
    parser.add_argument(
        "--always_recalculate", help="always recalculate", action="store_true"
    )
    parser.add_argument(
        "--keep_log", help="keep the log file from validation", action="store_true"
    )
    args = parser.parse_args()
    logger.setLevel(args.loglevel)

    message = {
        "pdbID": args.pdbid,
        "emdbID": args.emdbid,
        "outputRoot": args.output_root,
        "skipGzip": args.skip_gzip,
        "alwaysRecalculate": args.always_recalculate,
        "siteID": args.site_id,
        "pythonSiteID": args.python_site_id,
        "keepLog": args.keep_log,
    }

    runValidation().run_process(message=message)
