import time
from functools import partial
import textwrap

import date_time_utils as dutil


class RecordRetriever(object):
    def __init__(self, db_table, args):
        self.db_table = db_table
        self.args = args

    def get_rows_in_ts_range(self, ts1, ts2):
        rows = self.db_table.select('*', 
                'from_timestamp >= ts1 and to_timestamp <= ts2')
        return rows

    def display(self):
        if self.args.one:
            rows = self.get_rows_in_ts_range(
                    *dutil.parse_date_to_ts_range(*args.one))
            print(rows)

def get_rows_in_ts_range(db_table, tz, ts1, ts2):
    rows = db_table.select('*', 
            'from_timestamp >= %s and to_timestamp <= %s'%(ts1, ts2))
    return rows

def get_totals_in_ts_range(db_table, ts1, ts2):
    total_all = db_table.select_raw(
            'sum(to_timestamp-from_timestamp) as total_duration,'
            'sum(num_interruptions) as total_interruptions,'
            'sum(num_distractions) as total_distractions',
            'where from_timestamp >= %s and to_timestamp <= %s'%(ts1, ts2))
    total_by_work_type = db_table.select_raw(
            'work_type,'
            'sum(to_timestamp-from_timestamp) as total_duration,'
            'sum(num_interruptions) as total_interruptions,'
            'sum(num_distractions) as total_distractions',
            'where from_timestamp >= %s and to_timestamp <= %s '
            'group by work_type'%(ts1, ts2))
    total_by_day_type = db_table.select_raw(
            'day_type,'
            'sum(to_timestamp-from_timestamp) as total_duration,'
            'sum(num_interruptions) as total_interruptions,'
            'sum(num_distractions) as total_distractions',
            'where from_timestamp >= %s and to_timestamp <= %s '
            'group by day_type'%(ts1, ts2))
    return (total_all, total_by_work_type, total_by_day_type)

def get_disp_dict_from_total_row(r):
    # display dictionary
    dd = {}
    for k in r.keys():
        if k=='total_duration':
            total_dur_mins = r[k]/60.0
            total_dur_hours = total_dur_mins/60.0
            if total_dur_hours < 1:
                dd[k] = '%0.2f mins'%(total_dur_mins)
            else:
                dd[k] = '%0.2f hours'%(total_dur_hours)
        elif isinstance(r[k], float):
            dd[k] = "%0.2f"%(r[k])
        else:
            dd[k] = "%s"%(r[k])
    return dd

def get_disp_dict_from_row(tz, r):
    # display dictionary
    dd = {}
    dd['duration'] = str((r['to_timestamp'] - r['from_timestamp'])/60.0)
    (dd['from_date'], dd['from_time']) = dutil.ts_to_local_time(
            r['from_timestamp'], tz)
    (dd['to_date'], dd['to_time']) = dutil.ts_to_local_time(
            r['to_timestamp'], tz)
    dd['interruptions'] = "%si's"%(r['num_interruptions'])
    dd['distractions'] = "%sd's"%(r['num_distractions'])
    dd['task'] = r['task']
    dd['work_type'] = r['work_type']
    dd['day_type'] = r['day_type']
    return dd

def show_record(args, db_table, io):
    if args.oneday:
        ts_range = dutil.parse_date_to_ts_range(args.oneday,
                time.time(), args.timezone)
        rows = get_rows_in_ts_range(db_table, args.timezone, *ts_range)
        display_dicts = map(partial(get_disp_dict_from_row, args.timezone),
                rows)
        if not display_dicts:
            io.show_output("There are no results for this day")
            return
        io.show_output("Table for %s. day-type:%s  :"%(
            display_dicts[0]['from_date'], display_dicts[0]['day_type']))
        io.show_table(['from_time', 'to_time', 'duration', 'work_type',
            'interruptions', 'distractions', 'task'], display_dicts)
        (total_all, total_work_type, total_day_type) = get_totals_in_ts_range(
                db_table, *ts_range)
        all_disp_dict = map(get_disp_dict_from_total_row, total_all)
        work_type_disp_dict = map(get_disp_dict_from_total_row,
                total_work_type)
        day_type_disp_dict = map(get_disp_dict_from_total_row, total_day_type)
        io.show_table(['total_duration', 'total_interruptions',
            'total_distractions'], all_disp_dict)
        io.show_table(['work_type', 'total_duration', 'total_interruptions',
            'total_distractions'], work_type_disp_dict)

