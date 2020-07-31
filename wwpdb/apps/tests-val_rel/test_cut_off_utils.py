import unittest
from datetime import datetime

from wwpdb.apps.val_rel.utils.CutOffUtils import ok_to_copy, get_start_end_cut_off


class TestingTimeCutoff(unittest.TestCase):

    def setUp(self):
        weeknum = datetime.today().strftime("%U")
        this_year = datetime.today().strftime("%G")
        start_time = 'Thu:19:00:00'
        start_date = "{}:{}:{}".format(this_year, weeknum, start_time)
        self.start_cut_off_time = datetime.strptime(start_date, "%Y:%U:%a:%H:%M:%S")
        end_time = 'Sat:00:00:01'
        end_date = "{}:{}:{}".format(this_year, weeknum, end_time)
        self.end_cut_off_time = datetime.strptime(end_date, "%Y:%U:%a:%H:%M:%S")

    def test_ok_time(self):
        weeknum = datetime.today().strftime("%U")
        this_year = datetime.today().strftime("%G")
        timestr = 'Wed:19:00:00'
        mytime = "{}:{}:{}".format(this_year, weeknum, timestr)
        time_t = datetime.strptime(mytime, "%Y:%U:%a:%H:%M:%S")
        self.assertTrue(ok_to_copy(start_cut_off_time=self.start_cut_off_time,
                                   end_cut_off_time=self.end_cut_off_time,
                                   check_time=time_t
                                   ))

    def test_incorrect_time_thu(self):
        weeknum = datetime.today().strftime("%U")
        this_year = datetime.today().strftime("%G")
        timestr = 'Thu:20:00:00'
        mytime = "{}:{}:{}".format(this_year, weeknum, timestr)
        time_t = datetime.strptime(mytime, "%Y:%U:%a:%H:%M:%S")
        self.assertFalse(ok_to_copy(start_cut_off_time=self.start_cut_off_time,
                                    end_cut_off_time=self.end_cut_off_time,
                                    check_time=time_t
                                    ))

    def test_incorrect_time_fri(self):
        weeknum = datetime.today().strftime("%U")
        this_year = datetime.today().strftime("%G")
        timestr = 'Fri:06:00:00'
        mytime = "{}:{}:{}".format(this_year, weeknum, timestr)
        time_t = datetime.strptime(mytime, "%Y:%U:%a:%H:%M:%S")
        self.assertFalse(ok_to_copy(start_cut_off_time=self.start_cut_off_time,
                                    end_cut_off_time=self.end_cut_off_time,
                                    check_time=time_t
                                    ))

    def test_correct_time_after(self):
        weeknum = datetime.today().strftime("%U")
        this_year = datetime.today().strftime("%G")
        timestr = 'Sat:01:00:00'
        mytime = "{}:{}:{}".format(this_year, weeknum, timestr)
        time_t = datetime.strptime(mytime, "%Y:%U:%a:%H:%M:%S")
        self.assertTrue(ok_to_copy(start_cut_off_time=self.start_cut_off_time,
                                   end_cut_off_time=self.end_cut_off_time,
                                   check_time=time_t
                                   ))

    def test_get_start_end_cut_off(self):
        data = {'start': 'Thu:19:00:00',
                'end': 'Sat:00:01:00'
                }
        start, end = get_start_end_cut_off(cut_off_times=data)
        self.assertIsNotNone(start)
        self.assertIsNotNone(end)


if __name__ == '__main__':
    unittest.main()
