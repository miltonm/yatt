from __future__ import print_function
import sys
sys.path.append('..')

import unittest
import datetime
import calendar
import time
import pytz
import os

from worktracker.libworktracker import config
from worktracker.libworktracker import date_time_utils

class MockDb(object):
    pass

class TestDateTimeStuff(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_10_check_input_date(self):
        now_day = datetime.datetime(2014, 5, 12)
        ts = calendar.timegm(now_day.timetuple())
        d = date_time_utils.parse_date('today', ts)
        self.assertEqual(d, now_day.date())
        d = date_time_utils.parse_date('yesterday', ts)
        yesterday = now_day - datetime.timedelta(1)
        self.assertEqual(d, yesterday.date())
        someday = datetime.datetime(2013, 6, 13)
        d = date_time_utils.parse_date('13-6-2013', ts)
        self.assertEqual(d, someday.date())
        self.assertRaises(date_time_utils.DateTimeParsingError, 
                date_time_utils.parse_date, '13-0-2013', ts)

    def test_20_check_input_time(self):
        t = date_time_utils.parse_time('23:59')
        self.assertEqual(datetime.time(23, 59), t)
        self.assertRaises(date_time_utils.DateTimeParsingError, 
                date_time_utils.parse_time, '26:59')

    def test_30_check_parsing_date_time(self):
        tz_str = 'Europe/London'
        ts = date_time_utils.parse_date_time_to_ts('12-5-2014', '21:00', time.time(),
                tz_str)
        naive_utc = datetime.datetime.utcfromtimestamp(ts)
        utc_dt = pytz.utc.localize(naive_utc)
        local_tz = pytz.timezone(tz_str)
        local_dt = local_tz.normalize(utc_dt.astimezone(local_tz))
        self.assertEqual(
                local_tz.localize(datetime.datetime(2014, 5, 12, 21, 0)),
                local_dt)

    def test_40_check_parsing_date_to_ts_range(self):
        tz_str = 'Europe/London'
        (ts1, ts2) = date_time_utils.parse_date_to_ts_range('12-5-2014',
                time.time(),
                tz_str)
        naive_utc = datetime.datetime.utcfromtimestamp(ts1)
        utc_dt = pytz.utc.localize(naive_utc)
        local_tz = pytz.timezone(tz_str)
        local_dt = local_tz.normalize(utc_dt.astimezone(local_tz))
        self.assertEqual(
                local_tz.localize(datetime.datetime(2014, 5, 12, 0, 0)),
                local_dt)
        self.assertEqual(ts2, ts1+24*60*60-1)


if __name__ == '__main__':
    unittest.main()
