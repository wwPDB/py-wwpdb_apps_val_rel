import logging
import os

from wwpdb.apps.validation.src.scripts.star_to_cif import starToPdbx
from wwpdb.io.file.DataFile import DataFile

logger = logging.getLogger(__name__)


def convert_cs_file(entry_id, cs_file, model_file, working_dir):
    """convert star format CS file to CIF format for the validator"""

    if os.path.exists(cs_file):
        src_cs_file = os.path.join(working_dir, "input.cs")

        # We copy the cs_file to working directory so as to not uncompress in for_release directory
        df = DataFile(cs_file)
        df.copy(src_cs_file)

        cs_cif_file = os.path.join(working_dir, "working_cs.cif")

        if starToPdbx(
            entryId=entry_id, starPath=src_cs_file, pdbxPath=cs_cif_file, modelPath=model_file, remediation=True
        ):
            logger.info("CS star to cif conversion worked - new cs file: %s", cs_cif_file)

            return cs_cif_file

    logger.error("CS star to cif conversion failed")

    return None
