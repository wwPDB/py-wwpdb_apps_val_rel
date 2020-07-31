import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def parse_time(time_str):
    week_num = datetime.today().strftime("%U")
    this_year = datetime.today().strftime("%G")
    my_time = "{}:{}:{}".format(this_year, week_num, time_str)
    time_t = datetime.strptime(my_time, "%Y:%U:%a:%H:%M:%S")
    return time_t


def get_start_end_cut_off(cut_off_times):
    start_cut_off_time = parse_time(cut_off_times.get('start'))
    end_cut_off_time = parse_time(cut_off_times.get('end'))
    return start_cut_off_time, end_cut_off_time


def ok_to_copy(start_cut_off_time, end_cut_off_time, check_time):
    if start_cut_off_time < check_time < end_cut_off_time:
        logging.error('Do Not copy files - after cut off time point')
        return False
    logging.info('ok to copy files')
    return True
