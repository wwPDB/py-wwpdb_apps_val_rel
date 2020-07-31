import logging
import os

logger = logging.getLogger(__name__)


def already_run(test_file, output_folder):
    logging.info('checking for {}'.format(test_file))
    if test_file and output_folder:
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
