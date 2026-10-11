import logging
import os
import sys
from typing import Dict, List, Optional, TextIO, TypedDict, cast

from wwpdb.utils.config.ConfigInfo import getSiteId
from wwpdb.utils.dp.ValidationWrapper import ValidationWrapper

from wwpdb.apps.val_rel.config.ValConfig import ValConfig

logger = logging.getLogger(__name__)


class ValidationRunData(TypedDict):
    """Input data for ValidationRun.run()"""

    model: Optional[str]
    sf: Optional[str]
    cs: Optional[str]
    res: Optional[str]
    emvol: Optional[str]
    emxml: Optional[str]
    pdb_id: Optional[str]
    emdb_id: Optional[str]
    tempDir: Optional[str]
    entry_id: Optional[str]
    rundir: Optional[str]
    fsc: Optional[str]
    keeplog: bool
    logpath: Optional[str]
    outfiledict: Dict[str, str]
    entry_output_folder: Optional[str]


class ValidationRun:
    def __init__(self, siteId: Optional[str], verbose: bool = False, log: TextIO = sys.stderr) -> None:  # noqa: ARG002 pylint: disable=unused-argument
        if siteId is None:
            siteId = getSiteId()
        self.__siteid: str = siteId
        # self.__verbose = verbose
        vc = ValConfig(self.__siteid)
        self.__disablemulti = vc.val_disable_multithread

    def run(self, dD: ValidationRunData) -> List[Optional[str]]:
        """Produces a validation report based on data in the dD dictionry"""

        model = dD["model"]
        sfPath = dD["sf"]
        csPath = dD["cs"]
        resPath = dD["res"]
        volPath = dD["emvol"]
        emXmlPath = dD["emxml"]
        pdbid = dD["pdb_id"]
        emdbid = dD["emdb_id"]
        tempDir = dD["tempDir"]
        entry_id = dD["entry_id"]
        run_dir = dD["rundir"]
        fscPath = dD["fsc"]
        keepLog = dD["keeplog"]
        logPath = dD["logpath"]
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

        ok = vw.expList(dstPathList=cast(List[str], output_file_list))
        if not ok:
            logger.error("failed to copy files from %s to %s", run_dir, entry_output_folder)

        logger.info("validation run finished")

        # clean up temp folder after run
        vw.cleanup()

        return output_file_list
