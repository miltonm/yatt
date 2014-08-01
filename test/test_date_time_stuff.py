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

    def test_50_iso_to_gregorian(self):
        '''
        like the implementation I borrowed the testcases from the stackoverflow
        answer : http://stackoverflow.com/questions/304256/
        '''
        date1 = datetime.date(2005, 1, 1)
        date2 = datetime.date(2010, 1, 4)
        date3 = datetime.date(2010, 1, 3)
        self.assertEqual(date1, date_time_utils.iso_to_gregorian(
            *date1.isocalendar()))
        self.assertEqual(date2, date_time_utils.iso_to_gregorian(
            *date2.isocalendar()))
        self.assertEqual(date3, date_time_utils.iso_to_gregorian(
            *date3.isocalendar()))

    def test_60_check_ts_ranges_for_n_weeks(self):
        tz_str = "Europe/London"
        ts_ranges = date_time_utils.ts_ranges_for_last_n_weeks(
                3, 1406884383, tz_str)
        self.assertEqual(len(ts_ranges), 3)
        first_week_start = date_time_utils.ts_to_local_datetime(
                ts_ranges[0][0],
                tz_str)
        second_week_start = first_week_start + datetime.timedelta(days=7)
        second_week_start_ts = date_time_utils.date_time_to_ts(
                second_week_start.date(), second_week_start.time(), tz_str)
        self.assertEqual(ts_ranges[0][1], second_week_start_ts-1)
        self.assertEqual(ts_ranges[1][0], second_week_start_ts)
        third_week_start = second_week_start + datetime.timedelta(days=7)
        third_week_start_ts = date_time_utils.date_time_to_ts(
                third_week_start.date(), third_week_start.time(), tz_str
                )
        self.assertEqual(ts_ranges[1][1], third_week_start_ts-1)
        self.assertEqual(ts_ranges[2][0], third_week_start_ts)
        fourth_week_start = third_week_start + datetime.timedelta(days=7)
        fourth_week_start_ts = date_time_utils.date_time_to_ts(
                fourth_week_start.date(), fourth_week_start.time(), tz_str
                )
        self.assertEqual(ts_ranges[2][1], fourth_week_start_ts-1)

    def test_70_check_ts_range_for_current_week(self):
        tz_str = "Europe/London"
        ts_range = date_time_utils.ts_range_for_current_week_till_today(
                1406884383, tz_str)
        self.assertEqual(ts_range[0], 1406502000)
        self.assertEqual(ts_range[1], 1406934000-1)

if __name__ == '__main__':
    unittest.main()
