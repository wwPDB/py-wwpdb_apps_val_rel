import unittest
from datetime import datetime

from wwpdb.apps.val_rel.ValidateRelease import runValidation


class TestingTimeCutoff(unittest.TestCase):

    def setUp(self):
        self.rv = runValidation()
        self.rv.process_message(message={})

    def test_get_start_end(self):
        start, end = self.rv.get_start_end_cut_off()
        self.assertIsNotNone(start)
        self.assertIsNotNone(end)

    def test_ok_time(self):
        weeknum = datetime.today().strftime("%U")
        this_year = datetime.today().strftime("%G")
        timestr = 'Wed:19:00:00'
        mytime = "{}:{}:{}".format(this_year, weeknum, timestr)
        time_t = datetime.strptime(mytime, "%Y:%U:%a:%H:%M:%S")
        self.assertTrue(self.rv.is_ok_to_copy(now=time_t))

    def test_incorrect_time(self):
        weeknum = datetime.today().strftime("%U")
        this_year = datetime.today().strftime("%G")
        timestr = 'Thu:20:00:00'
        mytime = "{}:{}:{}".format(this_year, weeknum, timestr)
        time_t = datetime.strptime(mytime, "%Y:%U:%a:%H:%M:%S")
        self.assertFalse(self.rv.is_ok_to_copy(now=time_t))

    def test_correct_time_after(self):
        weeknum = datetime.today().strftime("%U")
        this_year = datetime.today().strftime("%G")
        timestr = 'Sat:01:00:00'
        mytime = "{}:{}:{}".format(this_year, weeknum, timestr)
        time_t = datetime.strptime(mytime, "%Y:%U:%a:%H:%M:%S")
        self.assertTrue(self.rv.is_ok_to_copy(now=time_t))

if __name__ == '__main__':
    unittest.main()
