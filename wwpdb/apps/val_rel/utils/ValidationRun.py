import logging
import os
import sys

from wwpdb.utils.dp.ValidationWrapper import ValidationWrapper
from wwpdb.apps.val_rel.config.ValConfig import ValConfig

logger = logging.getLogger(__name__)


class ValidationRun(object):
    def __init__(self, siteId, verbose=False, log=sys.stderr):
        self.__siteid = siteId
        self.__verbose = verbose
        vc = ValConfig(self.__siteid)
        self.__disablemulti = vc.val_disable_multithread

    def run(self, dD):
        """Produces a validation report based on data in the dD dictionry"""

        model = dD.get("model")
        sfPath = dD.get("sf")
        csPath = dD.get("cs")
        resPath = dD.get("res")
        volPath = dD.get("emvol")
        emXmlPath = dD.get("emxml")
        pdbid = dD.get("pdb_id")
        emdbid = dD.get("emdb_id")
        tempDir = dD.get("tempDir")
        entry_id = dD.get("entry_id")
        run_dir = dD.get("rundir")
        fscPath = dD.get("fsc")
        keepLog = dD.get("keeplog")
        logPath = dD.get("logpath")
        output_file_dict = dD["outfiledict"]
        entry_output_folder = dD["entry_output_folder"]

        logger.info("input files")
        logger.info("Site id: %s", self.__siteid)
        logger.info("model: %s", model)
        logger.info("SF: %s", sfPath)
        logger.info("cs: %s", csPath)
        logger.info("res: %s", resPath)
        logger.info("EM volume: %s", volPath)
        logger.info("EM XML: %s", emXmlPath)
        logger.info("FSC: %s", fscPath)
        logger.info("entry_id: %s", entry_id)
        logger.info("pdb_id: %s", pdbid)
        logger.info("emdb_id: %s", emdbid)

        vw = ValidationWrapper(
            tmpPath=tempDir,
            siteId=self.__siteid,
            verbose=False,
            log=sys.stderr,
        )

        vw.imp(model)
        vw.addInput(name="run_dir", value=run_dir)
        vw.addInput(name="request_validation_mode", value="release")
        if pdbid:
            vw.addInput(name="entry_id", value=pdbid)
        elif emdbid:
            vw.addInput(name="entry_id", value=emdbid)
            vw.addInput(name="emdb_id", value=emdbid)

        if sfPath is not None and os.access(sfPath, os.R_OK):
            vw.addInput(name="sf_file_path", value=sfPath)

        if csPath is not None and os.access(csPath, os.R_OK):
            vw.addInput(name="cs_file_path", value=csPath)

        if resPath is not None and os.access(resPath, os.R_OK):
            vw.addInput(name="nmr_restraint_file_path", value=resPath)

        if volPath is not None and os.access(volPath, os.R_OK):
            vw.addInput(name="vol_file_path", value=volPath)

        if emXmlPath is not None and os.access(emXmlPath, os.R_OK):
            vw.addInput(name="emdb_xml_path", value=emXmlPath)

        if fscPath is not None and os.access(fscPath, os.R_OK):
            vw.addInput(name="fsc_file_path", value=fscPath)

        if self.__disablemulti:
            vw.addInput(name="skip_multi", value=True)
        
        vw.setNumThreads(4)
        vw.setStartMemory(16000)
        vw.op("annot-wwpdb-validate-all-sf")
        # output log file
        if keepLog:
            vw.expLog(logPath)

        output_file_list = []
        # Keys needs to be in order of arguments - and must have something
        for key in ["pdf", "xml", "full_pdf", "png", "svg", "image_tar", "cif", "fofc", "2fofc"]:
            output_file_list.append(output_file_dict.get(key, None))

        logger.info(output_file_list)
        logger.info(output_file_dict)

        ok = vw.expList(dstPathList=output_file_list)
        if not ok:
            logger.error('failed to copy files from {} to {}'.format(run_dir, entry_output_folder))

        logger.info('validation run finished')

        # clean up temp folder after run
        vw.cleanup()

        return output_file_list
