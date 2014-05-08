''' 
As a general policy I  expect all inputs in utc and we do all calculations
in utc 
'''
from __future__ import print_function
import datetime
import pytz
import calendar
import time

class DateTimeParsingError(Exception):
    pass

def parse_date(date_str, now_timestamp):
    try:
        today_date = datetime.datetime.utcfromtimestamp(now_timestamp).date()
        if date_str == 'today':
            return today_date
        elif date_str == 'yesterday':
            return today_date - datetime.timedelta(days=1)
        else:
            (d, m, y) = map(int, date_str.split('-'))
            return datetime.date(y, m, d)
    except ValueError as v:
        msg = "Something went wrong parsing the date: %s"%(str(v))
        raise DateTimeParsingError(msg)

def parse_time(time_str):
    try:
        (h, m) = map(int, time_str.split(':'))
        return datetime.time(h, m)
    except ValueError as v:
        msg = "Something went wrong parsing the time: %s"%(str(v))
        raise DateTimeParsingError(msg)

def parse_date_to_ts_range(date_str, now_timestamp, tz_str):
    d = parse_date(date_str, now_timestamp)
    t = date_time_to_ts(d, datetime.time(0,0), tz_str)
    return (t, t+24*60*60-1)

def date_time_to_ts(d, t, tz_str):
    dt = datetime.datetime.combine(d, t)
    local_tz = pytz.timezone(tz_str)
    local_dt = local_tz.localize(dt)
    # to get timestamp from epoch from local time we could use
    # time.mktime() but in that case we're dependent on os defined
    # timezone (is that better ?). In this case we're manipulating timzone
    # from config and explicitly converting it to utc. By the way,
    # calendar.timegm assumes the the time tuple to be in UTC
    # alternative code:
    # local_dt.timetuple())
    # time.mktime(local_dt.timetuple())
    utc_dt = pytz.utc.normalize(local_dt.astimezone(pytz.utc))
    timestamp = calendar.timegm(utc_dt.timetuple())
    return timestamp
    
def parse_date_time_to_ts(date_str, time_str, now_timestamp, tz_str):
    d = parse_date(date_str, now_timestamp)
    t = parse_time(time_str)
    return date_time_to_ts(d, t, tz_str)

def ts_to_local_time(ts, tz_str):
    naive_utc_dt = datetime.datetime.utcfromtimestamp(ts)
    aware_utc_dt = pytz.utc.localize(naive_utc_dt)
    local_tz = pytz.timezone(tz_str)
    local_dt = local_tz.normalize(aware_utc_dt.astimezone(local_tz))
    date_str = local_dt.date().strftime('%d-%m-%Y')
    time_str = local_dt.time().strftime('%H:%M')
    return (date_str, time_str)


