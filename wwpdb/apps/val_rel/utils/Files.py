# Simple utilities for workign with files.

import gzip
import logging
import os
import shutil

logger = logging.getLogger(__name__)


def get_gzip_name(f):
    """Returns compressed filename"""
    return f + ".gz"


def gzip_file(in_file, input_folder, output_folder):
    """Compresses file in_file to in_file.gz.  Not be memory efficient as reads in file at one"""
    input_file = os.path.join(input_folder, in_file)
    output_file = os.path.join(output_folder, in_file)
    if os.path.exists(input_file):
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        with open(input_file, 'r') as f_in, gzip.open(get_gzip_name(output_file), "wb") as f_out:
            f_out.writelines(f_in)
        # os.unlink(input_file)


def copy_file(in_file, input_folder, output_folder):
    input_file = os.path.join(input_folder, in_file)
    output_file = os.path.join(output_folder, in_file)
    if os.path.exists(input_file):
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        shutil.copy(input_file, output_file)


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
