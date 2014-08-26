from __future__ import print_function
import libworktracker.date_time_utils as dutil

class Goal(object):
    def __init__(self, config, db_module, io, now_ts, args):
        ''' 
        inject db_module, config, io and now-timestamp. Also pass command
        line arguments as parsed and returned by ArgumentParser
        '''
        self.config = config
        self.db_module = db_module
        self.io = io
        self.now_ts = now_ts
        self.args = args
        self.db_goal_table = self.db_module.create_goal_table(
                self.config.db_full_path,
                self.io.log)
        self.db_record_table = db_module.create_record_table(
                self.config.db_full_path, self.io.log)

    def date_to_ts_range(self, date_str):
        return dutil.parse_date_to_ts_range(date_str, self.now_ts,
                self.config.timezone)

    def _show_set_goal_info(self):
        args = self.args
        io = self.io
        (_, end_ts) = self.date_to_ts_range(args.end_date)
        (_, today_end_ts) = self.date_to_ts_range("today")
        if end_ts <= today_end_ts:
            io.show_output("end_date of the goal should be later than today.")
        num_days = dutil.days_bet(args.start_date, args.end_date, self.now_ts)
        io.show_output("Number of days bet. start and end date: ", num_days)
        io.show_output("Number of hours per day from start date: ",
                (args.num_hours*1.0)/num_days)

    def _add_goal(self):
        args = self.args
        (start_ts, _) = self.date_to_ts_range(args.start_date)
        (_, end_ts) = self.date_to_ts_range(args.end_date)
        self.db_goal_table.insert(start_timestamp=start_ts, 
                end_timestamp = end_ts,
                num_hours = args.num_hours,
                work_type = args.work_type,
                name = args.name
                )

    def set_goal(self):
        self._show_set_goal_info()
        if self.io.get_confirmation('Happy with num hours ? (y/n) ',
                failure_text='Aborting goal!'):
            self._add_goal()

    def get_num_hours_done(self, work_type, ts1, ts2):
        total = self.db_record_table.select_raw(
                what_part = 'sum(to_timestamp-from_timestamp) as total_secs',
                end_part = 'where from_timestamp >= %s and to_timestamp <= %s'
                ' and work_type = "%s"'%(ts1, ts2, work_type)
                )
        total_secs = total[0]['total_secs'] or 0
        #total_hours = '%0.2f hours'%(total_secs/(60.0*60))
        return total_secs/(60.0*60)

    def get_disp_dict_from_row(self, r):
        dd = {}
        tz = self.config.timezone
        wt = r['work_type']
        start_ts = r['start_timestamp']
        end_ts = r['end_timestamp']
        hours_done = self.get_num_hours_done(wt, start_ts, end_ts)
        hours_left = r['num_hours'] - hours_done
        hours_done_str = '%0.2f hours'%(hours_done)
        hours_left_str = '%0.2f hours'%(hours_left)
        (last_day, _) = dutil.ts_to_local_date_time_strs(end_ts, tz)
        num_days_left = dutil.days_bet('today', last_day, self.now_ts)
        dd['name'] = r['name']
        dd['work-type'] = wt
        (dd['start'], _) = dutil.ts_to_local_date_time_strs(start_ts, tz)
        (dd['end'], _) = dutil.ts_to_local_date_time_strs(end_ts, tz)
        dd['hours-done'] = hours_done_str
        dd['hours-left'] = hours_left_str
        dd['days-left'] = str(num_days_left)
        dd['hours-per-day'] = (str((hours_left*1.0)/num_days_left)
                if num_days_left else 'failed')
        return dd

    def show_goals(self):
        rows = self.db_goal_table.select('*')
        display_dicts = map(self.get_disp_dict_from_row, rows)
        self.io.show_table(['name', 'work-type', 'start', 'end', 'hours-done',
            'hours-left', 'days-left', 'hours-per-day'],
                display_dicts, 120)

