import logging
import os

from wwpdb.io.file.DataFile import DataFile
from wwpdb.apps.validation.src.scripts.star_to_cif import starToPdbx
# For remediation
from wwpdb.utils.nmr.CifToNmrStar import CifToNmrStar
import tempfile

logger = logging.getLogger(__name__)


def __remediate_cs_file(infile, outfile):
    """Produces an NMR* formatted from input CIF.  Correcting missing section headers that are required"""
    ctns = CifToNmrStar()
    return ctns.convert(cifPath=infile, strPath=outfile)


def convert_star_to_cif(entry_id, star_file, cif_file):
    """Run the star to cif conversion from the validator package"""
    return starToPdbx(entryId=entry_id, starPath=star_file, pdbxPath=cif_file)


def convert_cs_file(entry_id, cs_file, working_dir):
    """convert star format CS file to CIF format for the validator"""
    if cs_file:
        if os.path.exists(cs_file):
            # We copy the cs_file to working directory so as to not uncompress in for_release directory and leave turd
            cs_file_tmp = os.path.join(working_dir, "input.cs")
            df = DataFile(cs_file)
            df.copy(cs_file_tmp)

            temp_cif_cs_file = os.path.join(working_dir, 'working_cs.cif')
            ok = convert_star_to_cif(entry_id=entry_id, star_file=cs_file_tmp, cif_file=temp_cif_cs_file)
            if ok and os.path.exists(temp_cif_cs_file):
                logger.info('CS star to cif conversion worked - new cs file: {}'.format(temp_cif_cs_file))

                # Until ftp archive remediated, we need to handle legacy CS files
                tempdPath = tempfile.mkdtemp(dir=os.path.dirname(temp_cif_cs_file))
                tempnmrstarPath = os.path.join(tempdPath, "working_cs.str")
                newcsPath = os.path.join(tempdPath, "working_cs.cif")
                __remediate_cs_file(temp_cif_cs_file, tempnmrstarPath)
                if os.path.exists(tempnmrstarPath):

                    ok = convert_star_to_cif(entry_id=entry_id, star_file=tempnmrstarPath, cif_file=newcsPath)
                    if ok and os.path.exists(newcsPath):
                        logger.info('CS star to cif conversion worked - new cs file: {}'.format(temp_cif_cs_file))
                        return newcsPath

                    logger.error('CS star to cif conversion failed')
            else:
                logger.error('CS star to cif conversion failed')

    return None
