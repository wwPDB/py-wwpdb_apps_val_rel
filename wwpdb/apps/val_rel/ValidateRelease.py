import argparse
import logging
import os
import shutil
import sys
import tempfile

from wwpdb.apps.validation.src.utils.minimal_map_cif import GenerateMinimalCif
from wwpdb.utils.config.ConfigInfo import ConfigInfo, getSiteId

from wwpdb.apps.val_rel.utils.Files import gzip_file, remove_files, copy_file
from wwpdb.apps.val_rel.utils.ValDataStore import ValDataStore
from wwpdb.apps.val_rel.utils.ValidationRun import ValidationRun
from wwpdb.apps.val_rel.utils.XmlInfo import XmlInfo
from wwpdb.apps.val_rel.utils.fileConversion import convert_star_to_cif
from wwpdb.apps.val_rel.utils.getFilesRelease import getFilesRelease
from wwpdb.apps.val_rel.utils.mmCIFInfo import mmCIFInfo
from wwpdb.apps.val_rel.utils.outputFiles import outputFiles

logger = logging.getLogger(__name__)


def is_simple_modification(model_path):
    """if there are only simple changes based the audit - skip calculation of validation report
    (currently, citation, citation_author and pdbx_audit_support)

    returns True is only simple changes present
    """

    SKIP_LIST = ['citation', 'citation_author', 'pdbx_audit_support']

    cf = mmCIFInfo(model_path)
    modified_cats = cf.get_latest_modified_categories()
    if modified_cats:
        for item in modified_cats:
            if item not in SKIP_LIST:
                return False

        logger.info('%s only a simple modification: %s', model_path, ','.join(modified_cats))
        return True
    return False


def already_run(test_file, output_folder):
    logging.info('checking for {}'.format(test_file))
    if test_file:
        if os.path.exists(test_file):
            if os.path.exists(output_folder):
                input_modification_time = os.path.getmtime(test_file)
                output_modification_time = os.path.getmtime(output_folder)
                if input_modification_time < output_modification_time:
                    logger.info("already run validation")
                    return True
                else:
                    logger.info("validation to be run")
                    return False
            else:
                logger.info("validation to be run")
                return False
        else:
            logger.info("missing input file - not running")
            return True
    else:
        logger.info("missing input file - not running")
        return True


class runValidation:
    def __init__(self):
        self.__keepLog = False
        self.__pdbid = None
        self.__emdbid = None
        self.__run_map_only = False
        self.__emdbids = []
        self.__pdbids = []
        self.__cI = None
        self.__pythonSiteID = None
        self.siteID = None
        # self.__da_internal = None
        self.__outputRoot = None
        self.__entry_id = None
        self.__modelPath = None
        self.__csPath = None
        self.__sfPath = None
        self.__emXmlPath = None
        self.__volPath = None
        self.__fscPath = None
        self.__tempDir = None
        self.__runDir = None
        self.__sessionPath = None
        # self.contour_level = None # not needed as its in the xml
        self.__entry_output_folder = None
        self.__temp_output_dir = None
        self.__validation_sub_folder = 'current'
        self.__pdb_output_folder = None
        self.__emdb_output_folder = None
        self.__entry_image_output_folder = None
        self.__validation_files_alternative_location = None
        self.__output_file_dict = {}
        self.__core_output_file_dict = {}
        self.__validation_xml = None

        self.__skip_gzip = False
        self.__skip_emdb = False
        self.__always_recalculate = False
        self.__remove_validation_files = False

        self.__rel_files = None
        self.__statefolder = None
        self.__vds = None
        self.__sds = None

    def setOutputRoot(self, outdir):
        self.__outputRoot = outdir

    def setPdbId(self, pdbid):
        self.__pdbid = pdbid

    def setEmdbId(self, emdbid):
        self.__emdbid = emdbid

    def setEmXmlPath(self, path):
        self.__emXmlPath = path

    def setAlwaysRecalculate(self, recalc):
        self.__always_recalculate = recalc

    def setModelPath(self, path):
        self.__modelPath = path

    def setPdbOutputFolder(self, path):
        self.__pdb_output_folder = path

    def setEmdbOutputFolder(self, path):
        self.__emdb_output_folder = path

    def getEntryOutputFolder(self):
        return self.__entry_output_folder

    def getEntryImageOutputFolder(self):
        return self.__entry_image_output_folder

    def getCoreOutputFileDict(self):
        return self.__core_output_file_dict

    def getValidationXml(self):
        return self.__validation_xml

    def getEntryId(self):
        return self.__entry_id

    @staticmethod
    def exptl_is_em(exp_methods):
        if "ELECTRON MICROSCOPY" in exp_methods or 'ELECTRON CRYSTALLOGRAPHY' in exp_methods:
            logger.info('is EM')
            return True
        return False

    def check_pdb_already_run(self):
        if self.__always_recalculate:
            return True
        modified = False
        if not already_run(self.__modelPath, self.__pdb_output_folder):
            if not is_simple_modification(self.__modelPath):
                modified = True
        if self.__sfPath:
            if self.__rel_files.is_sf_current():
                if not already_run(self.__sfPath, self.__pdb_output_folder):
                    modified = True
        if self.__csPath:
            if self.__rel_files.is_cs_current():
                if not already_run(self.__csPath, self.__pdb_output_folder):
                    modified = True
        return modified

    def check_emdb_already_run(self):
        if self.__always_recalculate:
            return True
        modified = False
        if self.__rel_files.is_em_xml_current():
            if not already_run(self.__emXmlPath, self.__emdb_output_folder):
                modified = True
        return modified

    def check_modified(self):
        self.set_output_dir_and_files()
        pdb_modified = self.check_pdb_already_run()
        emdb_modified = self.check_emdb_already_run()

        if pdb_modified or emdb_modified:
            return True
        return False

    def get_emdb_pdb_string(self):
        emdb_pdb_string = ''
        if self.__emdbid and self.__pdbid:
            emdb_pdb_string = '{}-{}'.format(self.__emdbid, self.__pdbid)
        return emdb_pdb_string

    def set_output_dir_and_files(self):
        of = outputFiles(
            pdbID=self.__pdbid,
            emdbID=self.__emdbid,
            siteID=self.siteID,
            outputRoot=self.__outputRoot,
            validation_sub_directory=self.__validation_sub_folder,
            temp_output_folder=self.__temp_output_dir
        )
        self.__entry_output_folder = of.get_entry_output_folder()
        logger.info("output folder: %s", self.__entry_output_folder)
        self.__entry_image_output_folder = of.get_pdb_validation_images_output_folder()
        self.__core_output_file_dict = of.get_core_validation_files()
        self.__validation_files_alternative_location = of.get_validation_files_for_separate_location()
        self.__validation_xml = of.get_validation_xml()
        self.__output_file_dict = of.get_all_validation_files()
        self.__pdb_output_folder = of.get_pdb_output_folder()
        self.__emdb_output_folder = of.get_emdb_output_folder()
        self.__statefolder = of.get_root_state_folder()

    def process_message(self, message):
        logger.info("Message received %s", message)
        self.__pdbid = message.get("pdbID")
        if self.__pdbid:
            self.__pdbid = self.__pdbid.lower()
        self.__emdbid = message.get("emdbID")
        if self.__emdbid:
            self.__emdbid = self.__emdbid.upper()
        self.siteID = message.get("siteID")
        if not self.siteID:
            self.siteID = getSiteId()
        self.__outputRoot = message.get("outputRoot")
        self.__skip_gzip = message.get("skipGzip", False)
        self.__skip_emdb = message.get('skip_emdb', False)
        self.__always_recalculate = message.get("alwaysRecalculate", False)
        self.__keepLog = message.get("keepLog", False)
        self.__validation_sub_folder = message.get("subfolder", 'current')
        self.__remove_validation_files = message.get('removeValFiles', False)
        self.__pythonSiteID = message.get("python_site_id", self.siteID)
        self.__cI = ConfigInfo(self.siteID)
        self.__entry_output_folder = None

    def set_entry_id(self):
        if self.__pdbid:
            self.__entry_id = self.__pdbid
        elif self.__emdbid:
            self.__entry_id = self.__emdbid
        else:
            logger.error("No PDB or EMDB provided")
            return False
        return True

    def run_process(self, message):
        """Process message and act on it"""

        self.process_message(message)
        ret = self.set_entry_id()
        if not ret:
            return False

        self.__temp_output_dir = None
        self.set_output_dir_and_files()  # To get statefolder and prepare for removal
        if self.__remove_validation_files:
            self.remove_existing_files()
            return True

        # If validation already running skip - will reschedule later
        self.__sds = ValDataStore(self.__entry_id, self.__statefolder)
        if self.__sds.isValidationRunning is True:
            logger.info("Skipping run of %s as run in progress", self.__entry_id)
            return True

        logger.info("running validation for %s, %s", self.__pdbid, self.__emdbid)

        self.__rel_files = getFilesRelease(siteID=self.siteID)

        # worked = False
        self.__sessionPath = self.__cI.get("SITE_WEB_APPS_SESSIONS_PATH")
        if not os.path.exists(self.__sessionPath):
            os.makedirs(self.__sessionPath)
        self.__runDir = tempfile.mkdtemp(
            dir=self.__sessionPath,
            prefix="{}_validation_release_".format(self.__entry_id),
        )
        self.__tempDir = tempfile.mkdtemp(
            dir=self.__runDir,
            prefix="{}_validation_release_temp_dir_".format(self.__entry_id),
        )
        self.__temp_output_dir = tempfile.mkdtemp(
            dir=self.__runDir,
            prefix="%s_validation_release_output_dir_" % self.__entry_id
        )
        self.set_output_dir_and_files()

        all_worked = []
        run_pdb = []
        run_emdb = []
        run_emdb_and_pdbid = []

        if self.__emdbid:
            self.__emXmlPath = self.__rel_files.get_emdb_xml(self.__emdbid)
            self.__volPath = self.__rel_files.get_emdb_volume(self.__emdbid)
            if self.__volPath:
                self.__run_map_only = True

        if self.__pdbid:
            self.__modelPath = self.__rel_files.get_model(self.__pdbid)
            self.__sfPath = self.__rel_files.get_sf(self.__pdbid)
            self.__csPath = self.__rel_files.get_cs(self.__pdbid)
            if not self.__csPath:
                self.__csPath = self.__rel_files.get_nmr_data(self.__pdbid)

            cf = mmCIFInfo(self.__modelPath)
            exp_methods = cf.get_exp_methods()
            if self.exptl_is_em(exp_methods) and not self.__skip_emdb:
                if not self.__emdbid:
                    self.__emdbid = cf.get_associated_emdb()
                    run_emdb.append(self.__emdbid)
                    run_emdb_and_pdbid.append(self.get_emdb_pdb_string())

            run_pdb.append(self.__pdbid)
            worked = self.run_validation()
            all_worked.append(worked)

        if self.__emdbid:
            if self.__emdbid not in run_emdb:
                if self.__volPath:
                    # da_internal_pdbids = self.da_internal.selectData('PDBIDs_FROM_ASSOC_EMDBID', self.__emdbid)
                    # logging.info('data from da_internal')
                    # logger.info(da_internal_pdbids)
                    self.__pdbids = XmlInfo(self.__emXmlPath).get_pdbids_from_xml()
                    if self.__pdbids:
                        for self.__pdbid in self.__pdbids:
                            self.__pdbid = self.__pdbid.lower()
                            if self.get_emdb_pdb_string() not in run_emdb_and_pdbid:
                                self.__modelPath = self.__rel_files.get_model(self.__pdbid)
                                if self.__modelPath:
                                    # run validation
                                    worked = self.run_validation()
                                    all_worked.append(worked)
                            else:
                                logger.info('report already run for %s', self.get_emdb_pdb_string())

        if self.__run_map_only:
            logger.info('{} make map only validation report without models'.format(self.__emdbid))
            self.__pdbid = None
            self.set_output_dir_and_files()
            self.__modelPath = os.path.join(
                self.__tempDir, "{}_minimal.cif".format(self.__emdbid)
            )
            logger.info('generating minimal cif: {}'.format(self.__modelPath))
            GenerateMinimalCif(emdb_xml=self.__emXmlPath).write_out(
                output_cif=self.__modelPath
            )
            # run validation
            worked = self.run_validation()
            logger.info('map only validation worked: {}'.format(worked))
            all_worked.append(worked)

        if list(set(all_worked)) == [True]:
            return True
        else:
            logger.error(all_worked)
            return False

    def remove_existing_files(self):
        """Removes existing validation files"""
        self.set_output_dir_and_files()
        remove_files(list(self.__output_file_dict.values()))
        if self.__emdbid:
            em_of = outputFiles(
                pdbID=self.__pdbid,
                emdbID=self.__emdbid,
                siteID=self.siteID,
                outputRoot=self.__outputRoot,
                validation_sub_directory=self.__validation_sub_folder
            )
            em_of.set_accession_variables(with_emdb=True)
            emdb_output_file_dict = em_of.get_core_validation_files()
            remove_files(emdb_output_file_dict.values())

    def copy_to_emdb(self, copy_to_root_emdb=False):
        if self.__emdbid:
            temp_output_dir = tempfile.mkdtemp(
                dir=self.__sessionPath,
                prefix="%s_validation_release_emdb_temp_output_dir_" % self.__entry_id
            )
            of = outputFiles(
                pdbID=self.__pdbid,
                emdbID=self.__emdbid,
                siteID=self.siteID,
                outputRoot=self.__outputRoot,
                temp_output_folder=temp_output_dir,
                validation_sub_directory=self.__validation_sub_folder
            )
            logger.info("EMDB ID: %s", self.__emdbid)
            __emdb_output_folder = of.get_emdb_output_folder()
            if __emdb_output_folder != self.__entry_output_folder:
                logger.info("EMDB output folder: %s", __emdb_output_folder)
                of.set_accession_variables(
                    with_emdb=True, copy_to_root_emdb=copy_to_root_emdb
                )
                emdb_output_file_dict = of.get_core_validation_files()
                logger.info("EMDB output file dict: %s", emdb_output_file_dict)

                for k in self.__output_file_dict:
                    if k in emdb_output_file_dict:
                        in_file = self.__output_file_dict[k]
                        em_in_file = emdb_output_file_dict[k]
                        if os.path.exists(in_file):
                            shutil.copy(in_file, em_in_file)
                if self.__skip_gzip:
                    for f in emdb_output_file_dict.values():
                        copy_file(in_file=f,
                                  output_folder=__emdb_output_folder)

                else:
                    for f in emdb_output_file_dict.values():
                        gzip_file(in_file=f,
                                  output_folder=__emdb_output_folder)

        return True

    @staticmethod
    def __gzip_output(filelist, output_folder):
        """Compresses list of files"""
        logger.debug('gzip files: {}'.format(filelist))
        for f in filelist:
            gzip_file(in_file=f, output_folder=output_folder)

    @staticmethod
    def __copy_output(filelist, output_folder):
        """Compresses list of files"""
        logger.debug('copy files: {}'.format(filelist))
        for f in filelist:
            copy_file(in_file=f, output_folder=output_folder)

    def convert_cs_file(self):
        """convert star format CS file to CIF format for the validator"""
        if self.__csPath:
            if os.path.exists(self.__csPath):
                temp_cif_cs_file = os.path.join(self.__tempDir, self.__pdbid + 'cs.cif')
                ok = convert_star_to_cif(star_file=self.__csPath, cif_file=temp_cif_cs_file)
                if ok and os.path.exists(temp_cif_cs_file):
                    self.__csPath = temp_cif_cs_file
                    logger.info('CS star to cif conversion worked - new cs file: {}'.format(self.__csPath))
                    return True
                else:
                    logger.error('CS star to cif conversion failed')

        return False

    def run_validation(self):

        self.__sds.setValidationRunning(True)
        try:
            if self.__emdbid:
                if not self.__emXmlPath:
                    self.__emXmlPath = self.__rel_files.get_emdb_xml(self.__emdbid)
                self.__volPath = self.__rel_files.get_emdb_volume(self.__emdbid)
                self.__fscPath = self.__rel_files.get_emdb_fsc(self.__emdbid)
            if self.__pdbid:
                self.__sfPath = self.__rel_files.get_sf(self.__pdbid)
                self.__csPath = self.__rel_files.get_cs(self.__pdbid)
                if self.__csPath:
                    ok = self.convert_cs_file()
                    if not ok:
                        logger.error('CS star to cif conversion failed')
                        self.__sds.setValidationRunning(False)
                        return False

            # check if any input files have changed and set output folders
            is_modified = self.check_modified()
            if not is_modified:
                logger.info("skipping %s/%s as entry files have not changed",
                            self.__pdbid, self.__emdbid)

                self.__sds.setValidationRunning(False)
                return True

            logger.info("Entry output folder: %s", self.__entry_output_folder)

            # clearing existing reports before making new ones
            self.remove_existing_files()

            run_dir = tempfile.mkdtemp(
                dir=self.__runDir,
                prefix="%s_validation_release_rundir_" % self.__entry_id
            )

            log_path = os.path.join(self.__temp_output_dir, "validation.log")

            logger.info("input files")
            logger.info("model: %s", self.__modelPath)
            logger.info("SF: %s", self.__sfPath)
            logger.info("cs: %s", self.__csPath)
            logger.info("EM volume: %s", self.__volPath)
            logger.info("EM XML: %s", self.__emXmlPath)
            logger.info("entry_id: %s", self.__entry_id)
            logger.info("pdb_id: %s", self.__pdbid)
            logger.info("emdb_id: %s", self.__emdbid)

            dD = {
                "model": self.__modelPath,
                "sf": self.__sfPath,
                "cs": self.__csPath,
                "emvol": self.__volPath,
                "emxml": self.__emXmlPath,
                "pdb_id": self.__pdbid,
                "entry_id": self.__entry_id,
                "emdb_id": self.__emdbid,
                "tempDir": self.__tempDir,
                "rundir": run_dir,
                "fsc": self.__fscPath,
                "keeplog": self.__keepLog,
                "logpath": log_path,
                "outfiledict": self.__output_file_dict,
                # "entry_output_folder": self.__entry_output_folder,
                "entry_output_folder": self.__temp_output_dir,
            }

            vr = ValidationRun(siteId=self.__pythonSiteID, verbose=False, log=sys.stderr)
            output_file_list = vr.run(dD)
            logger.info("Returning with %s", output_file_list)

            # make output directory if it doesn't exist
            if not os.path.exists(self.__entry_output_folder):
                os.makedirs(self.__entry_output_folder)
            else:
                # Set the time on output_folder to now
                os.utime(self.__entry_output_folder, None)

            if self.__pdbid and self.__emdbid:
                ok = self.copy_to_emdb()
                if not ok:
                    logger.error("failed to copy to emdb folder")
                    self.__sds.setValidationRunning(False)
                    return False

            output_file_list = []
            for key in self.__output_file_dict:
                if key not in self.__validation_files_alternative_location:
                    output_file_list.append(self.__output_file_dict.get(key, None))

            output_file_list_to_alternative_location = self.__validation_files_alternative_location.values()

            logger.info('files to copy to {}: {}'.format(self.__entry_output_folder, ','.join(output_file_list)))
            logger.info('files to copy to {}: {}'.format(self.__entry_image_output_folder,
                                                          ','.join(output_file_list_to_alternative_location)))

            if self.__skip_gzip:
                self.__copy_output(filelist=output_file_list,
                                   output_folder=self.__entry_output_folder)
                self.__copy_output(filelist=output_file_list_to_alternative_location,
                                   output_folder=self.__entry_image_output_folder)

            else:
                self.__gzip_output(filelist=output_file_list,
                                   output_folder=self.__entry_output_folder)
                self.__gzip_output(filelist=output_file_list_to_alternative_location,
                                   output_folder=self.__entry_image_output_folder)



            self.__sds.setValidationRunning(False)
            return True

        except Exception as e:
            logger.exception(e)
            self.__sds.setValidationRunning(False)
            return False


def main():
    log_format = "%(asctime)s [%(levelname)s]-%(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(format=log_format)

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
    parser.add_argument(
        "--remove_files", help="clear out the existing files for a validation run", action="store_true"
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
        "keepLog": args.keep_log,
        "removeValFiles": args.remove_files,
    }

    # If pass in None - overrides siteid
    if args.python_site_id:
        message["pythonSiteID"] = args.python_site_id,

    runValidation().run_process(message=message)


if "__main__" in __name__:
    main()
