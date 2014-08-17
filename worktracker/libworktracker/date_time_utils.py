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
    '''
    d: date
    t: time
    tz_str: timezone str
    return timestamp created from combined date, time and timezone
    '''
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

def ts_to_local_datetime(ts, tz_str):
    naive_utc_dt = datetime.datetime.utcfromtimestamp(ts)
    aware_utc_dt = pytz.utc.localize(naive_utc_dt)
    local_tz = pytz.timezone(tz_str)
    local_dt = local_tz.normalize(aware_utc_dt.astimezone(local_tz))
    return local_dt

def ts_to_local_date_time_strs(ts, tz_str):
    local_dt = ts_to_local_datetime(ts, tz_str)
    date_str = local_dt.date().strftime('%d-%m-%Y')
    time_str = local_dt.time().strftime('%H:%M')
    return (date_str, time_str)

# copied the following routines from stackoverflow
# http://stackoverflow.com/questions/304256/
def _iso_year_start(iso_year):
    "The gregorian calendar date of the first day of the given ISO year"
    fourth_jan = datetime.date(iso_year, 1, 4)
    delta = datetime.timedelta(fourth_jan.isoweekday()-1)
    return fourth_jan - delta 

def iso_to_gregorian(iso_year, iso_week, iso_day):
    "Gregorian calendar date for the given ISO year, week and day"
    year_start = _iso_year_start(iso_year)
    return year_start + datetime.timedelta(days=iso_day-1, weeks=iso_week-1)

def week_boundaries_to_ts_range(first_day_of_week_date, last_day_of_week_date,
        tz_str):
    zt = datetime.time(0,0)
    return (
            date_time_to_ts(first_day_of_week_date, zt, tz_str),
            (date_time_to_ts(last_day_of_week_date, zt, tz_str)+24*60*60-1)
            )

def ts_range_for_current_week_till_today(now_timestamp, tz_str):
    today_local_date = ts_to_local_datetime(now_timestamp, tz_str).date()
    (y, wn, wd) = today_local_date.isocalendar()
    conv = iso_to_gregorian
    return week_boundaries_to_ts_range(conv(y, wn, 1), conv(y, wn, wd), tz_str)

def ts_ranges_for_last_n_weeks(n, now_timestamp, tz_str):
    today_local_date = ts_to_local_datetime(now_timestamp, tz_str).date()
    (y, wn, wd) = today_local_date.isocalendar()
    if n >= wn:
        raise(Exception("Cant handle dates across years yet"))
    conv = iso_to_gregorian
    last_n_weeks = [(conv(y, i, 1), conv(y, i, 7)) for i in range(wn-n, wn)]
    return [ week_boundaries_to_ts_range(*date_pair, tz_str=tz_str)
            for date_pair in last_n_weeks ]

def ts_ranges_for_last_n_days(n, now_timestamp, tz):
    (start_of_today, _ ) = parse_date_to_ts_range("today", now_timestamp, tz)
    eoy = start_of_today - 1
    day_in_secs = 24*60*60
    return ( (start_ts, start_ts+day_in_secs-1) 
            for start_ts in xrange(start_of_today-n*day_in_secs,
                start_of_today, day_in_secs))





