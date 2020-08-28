import logging
import os

from wwpdb.io.file.DataFile import DataFile
from wwpdb.apps.validation.src.scripts.star_to_cif import starToPdbx

logger = logging.getLogger(__name__)


def convert_star_to_cif(star_file, cif_file):
    """Run the star to cif conversion from the validator package"""
    return starToPdbx(starPath=star_file, pdbxPath=cif_file)


def convert_cs_file(cs_file, working_dir):
    """convert star format CS file to CIF format for the validator"""
    if cs_file:
        if os.path.exists(cs_file):
            # We copy the cs_file to working directory so as to not uncompress in for_release directory and leave turd
            cs_file_tmp = os.path.join(working_dir, "input.cs")
            df = DataFile(cs_file)
            df.copy(cs_file_tmp)

            temp_cif_cs_file = os.path.join(working_dir, 'working_cs.cif')
            ok = convert_star_to_cif(star_file=cs_file_tmp, cif_file=temp_cif_cs_file)
            if ok and os.path.exists(temp_cif_cs_file):
                logger.info('CS star to cif conversion worked - new cs file: {}'.format(temp_cif_cs_file))
                return temp_cif_cs_file
            else:
                logger.error('CS star to cif conversion failed')

    return None
