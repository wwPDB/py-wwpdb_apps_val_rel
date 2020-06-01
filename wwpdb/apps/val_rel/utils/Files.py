# Simple utilities for workign with files.

import gzip
import logging
import os
import shutil

logger = logging.getLogger(__name__)


def get_gzip_name(f):
    """Returns compressed filename"""
    return f + ".gz"


def gzip_file(in_file, output_folder):
    """Compresses file in_file to in_file.gz.  Not be memory efficient as reads in file at one"""
    output_gzipped_file = get_gzip_name(in_file)
    if os.path.exists(in_file):
        with open(in_file, 'r') as f_in, gzip.open(output_gzipped_file, "wb") as f_out:
            f_out.writelines(f_in)
        if os.path.exists(output_gzipped_file):
            copy_file(in_file=output_gzipped_file, output_folder=output_folder)


def copy_file(in_file, output_folder):
    input_filename = os.path.basename(in_file)
    output_file = os.path.join(output_folder, input_filename)
    if os.path.exists(in_file):
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        shutil.copy(in_file, output_file)


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
