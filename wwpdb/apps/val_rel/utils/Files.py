# Simple utilities for workign with files.

import os
import gzip
import logging
import gzip

logger = logging.getLogger(__name__)


def get_gzip_name(f):
    """Returns compressed filename"""
    return f + ".gz"


def gzip_file(in_file):
    """Compresses file in_file to in_file.gz.  Right not be memory efficient"""
    if os.path.exists(in_file):
        with open(in_file, 'r') as f_in, gzip.open(get_gzip_name(in_file), "wb") as f_out:
            f_out.writelines(f_in)
        os.unlink(in_file)


def remove_files(file_list):
    """Removes a list of files if present"""
    if file_list:
        logger.debug("removing existing files")
        logger.debug(file_list)
        for f in file_list:
            if os.path.exists(f):
                os.remove(f)
            gzip_f = get_gzip_name(f)
            if os.path.exists(gzip_f):
                os.remove(gzip_f)
