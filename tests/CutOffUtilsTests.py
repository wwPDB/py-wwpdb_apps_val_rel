import unittest
from datetime import datetime

from wwpdb.apps.val_rel.utils.CutOffUtils import get_start_end_cut_off, ok_to_copy


class TestingTimeCutoff(unittest.TestCase):
    def setUp(self) -> None:
        weeknum = datetime.today().strftime("%U")  # noqa: DTZ002
        this_year = datetime.today().strftime("%G")  # noqa: DTZ002
        start_time = "Thu:19:00:00"
        start_date = f"{this_year}:{weeknum}:{start_time}"
        self.start_cut_off_time = datetime.strptime(start_date, "%Y:%U:%a:%H:%M:%S")  # noqa: DTZ007
        end_time = "Sat:00:00:01"
        end_date = f"{this_year}:{weeknum}:{end_time}"
        self.end_cut_off_time = datetime.strptime(end_date, "%Y:%U:%a:%H:%M:%S")  # noqa: DTZ007

    def test_ok_time(self) -> None:
        weeknum = datetime.today().strftime("%U")  # noqa: DTZ002
        this_year = datetime.today().strftime("%G")  # noqa: DTZ002
        timestr = "Wed:19:00:00"
        mytime = f"{this_year}:{weeknum}:{timestr}"
        time_t = datetime.strptime(mytime, "%Y:%U:%a:%H:%M:%S")  # noqa: DTZ007
        self.assertTrue(
            ok_to_copy(
                start_cut_off_time=self.start_cut_off_time, end_cut_off_time=self.end_cut_off_time, check_time=time_t
            )
        )

    def test_incorrect_time_thu(self) -> None:
        weeknum = datetime.today().strftime("%U")  # noqa: DTZ002
        this_year = datetime.today().strftime("%G")  # noqa: DTZ002
        timestr = "Thu:20:00:00"
        mytime = f"{this_year}:{weeknum}:{timestr}"
        time_t = datetime.strptime(mytime, "%Y:%U:%a:%H:%M:%S")  # noqa: DTZ007
        self.assertFalse(
            ok_to_copy(
                start_cut_off_time=self.start_cut_off_time, end_cut_off_time=self.end_cut_off_time, check_time=time_t
            )
        )

    def test_incorrect_time_fri(self) -> None:
        weeknum = datetime.today().strftime("%U")  # noqa: DTZ002
        this_year = datetime.today().strftime("%G")  # noqa: DTZ002
        timestr = "Fri:06:00:00"
        mytime = f"{this_year}:{weeknum}:{timestr}"
        time_t = datetime.strptime(mytime, "%Y:%U:%a:%H:%M:%S")  # noqa: DTZ007
        self.assertFalse(
            ok_to_copy(
                start_cut_off_time=self.start_cut_off_time, end_cut_off_time=self.end_cut_off_time, check_time=time_t
            )
        )

    def test_correct_time_after(self) -> None:
        weeknum = datetime.today().strftime("%U")  # noqa: DTZ002
        this_year = datetime.today().strftime("%G")  # noqa: DTZ002
        timestr = "Sat:01:00:00"
        mytime = f"{this_year}:{weeknum}:{timestr}"
        time_t = datetime.strptime(mytime, "%Y:%U:%a:%H:%M:%S")  # noqa: DTZ007
        self.assertTrue(
            ok_to_copy(
                start_cut_off_time=self.start_cut_off_time, end_cut_off_time=self.end_cut_off_time, check_time=time_t
            )
        )

    def test_get_start_end_cut_off(self) -> None:
        data = {"start": "Thu:19:00:00", "end": "Sat:00:01:00"}
        start, end = get_start_end_cut_off(cut_off_times=data)
        self.assertIsNotNone(start)
        self.assertIsNotNone(end)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
