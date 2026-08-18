import logging
from datetime import datetime
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


def parse_time(time_str: str) -> datetime:
    week_num = datetime.today().strftime("%U")  # noqa: DTZ002
    this_year = datetime.today().strftime("%G")  # noqa: DTZ002
    my_time = f"{this_year}:{week_num}:{time_str}"
    time_t = datetime.strptime(my_time, "%Y:%U:%a:%H:%M:%S")  # noqa: DTZ007
    return time_t


def get_start_end_cut_off(cut_off_times: Dict[str, str]) -> Tuple[datetime, datetime]:
    stime = cut_off_times.get("start")
    etime = cut_off_times.get("end")
    if stime is None or etime is None:
        emsg = f"Cutoff times not available {stime}, {etime}"
        raise ValueError(emsg)
    start_cut_off_time = parse_time(stime)
    end_cut_off_time = parse_time(etime)
    return start_cut_off_time, end_cut_off_time


def ok_to_copy(start_cut_off_time: datetime, end_cut_off_time: datetime, check_time: datetime) -> bool:
    if start_cut_off_time < check_time < end_cut_off_time:
        logger.error("Do Not copy files - after cut off time point")
        return False
    logger.info("ok to copy files")
    return True
