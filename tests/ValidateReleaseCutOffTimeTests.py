import unittest
from datetime import datetime
from unittest.mock import patch

if __package__ is None or __package__ == "":
    import sys
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import StandardConfig  # type: ignore[import-not-found]  # pylint: disable=import-error
else:
    from .commonsetup import (  # noqa: TID252  # pragma: no cover
        StandardConfig,
    )

from wwpdb.apps.val_rel.ValidateRelease import runValidation


class TestingTimeCutoff(unittest.TestCase):
    def setUp(self) -> None:
        with patch("wwpdb.utils.config.ConfigInfoApp.ConfigInfo", side_effect=StandardConfig) as _mock_method:  # noqa: F841
            self.rv = runValidation()
            self.rv.process_message(message={})

    def test_get_start_end(self) -> None:
        start, end = self.rv.get_start_end_cut_off()
        self.assertIsNotNone(start)
        self.assertIsNotNone(end)

    def test_ok_time(self) -> None:
        weeknum = datetime.today().strftime("%U")  # noqa: DTZ002
        this_year = datetime.today().strftime("%G")  # noqa: DTZ002
        timestr = "Wed:19:00:00"
        mytime = f"{this_year}:{weeknum}:{timestr}"
        time_t = datetime.strptime(mytime, "%Y:%U:%a:%H:%M:%S")  # noqa: DTZ007
        self.assertTrue(self.rv.is_ok_to_copy(now=time_t))

    def test_correct_time_thu(self) -> None:
        # Cutoff is Friday from 9am on
        weeknum = datetime.today().strftime("%U")  # noqa: DTZ002
        this_year = datetime.today().strftime("%G")  # noqa: DTZ002
        timestr = "Thu:20:00:00"
        mytime = f"{this_year}:{weeknum}:{timestr}"
        time_t = datetime.strptime(mytime, "%Y:%U:%a:%H:%M:%S")  # noqa: DTZ007
        self.assertTrue(self.rv.is_ok_to_copy(now=time_t))

    def test_incorrect_time_fri(self) -> None:
        weeknum = datetime.today().strftime("%U")  # noqa: DTZ002
        this_year = datetime.today().strftime("%G")  # noqa: DTZ002
        timestr = "Fri:09:01:00"
        mytime = f"{this_year}:{weeknum}:{timestr}"
        time_t = datetime.strptime(mytime, "%Y:%U:%a:%H:%M:%S")  # noqa: DTZ007
        self.assertFalse(self.rv.is_ok_to_copy(now=time_t))

    def test_correct_time_after(self) -> None:
        weeknum = datetime.today().strftime("%U")  # noqa: DTZ002
        this_year = datetime.today().strftime("%G")  # noqa: DTZ002
        timestr = "Sat:01:00:00"
        mytime = f"{this_year}:{weeknum}:{timestr}"
        time_t = datetime.strptime(mytime, "%Y:%U:%a:%H:%M:%S")  # noqa: DTZ007
        self.assertTrue(self.rv.is_ok_to_copy(now=time_t))

    # def test_now(self):
    #    # this test will be disabled - just for testing development
    #    time_t = datetime.now()
    #    self.assertTrue(self.rv.is_ok_to_copy(now=time_t))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
