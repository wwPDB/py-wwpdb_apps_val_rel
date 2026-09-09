import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


def already_run(test_file: Optional[str], output_folder: Optional[str]) -> bool:
    """Returns True if the test_file is earlier than the output_older has been updated."""
    logger.info("checking for %s", test_file)
    if test_file and output_folder:
        if os.path.exists(test_file):
            if os.path.exists(output_folder):
                input_modification_time = os.path.getmtime(test_file)
                output_modification_time = os.path.getmtime(output_folder)
                if input_modification_time < output_modification_time:
                    logger.info("already run validation")
                    return True
                logger.info("validation to be run")
                return False
            logger.info("validation to be run")
            return False
        logger.info("missing input file %s - not running", test_file)
        return True
    logger.info("missing input file - %s - not running", test_file)
    return True
