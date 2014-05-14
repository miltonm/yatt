from __future__ import print_function
import argparse
import time


from libworktracker import date_time_utils

def main(config, db_module, show_output_fn, logging_fn, now_timestamp,
        test_args = None):
    def in_seconds(arg_val):
        arg_val_min = float(arg_val)
        return int(arg_val_min*60)
    parser = argparse.ArgumentParser()
    parser.add_argument("date",
            help="<dd-mm-yyyy>/yesterday/today",
            metavar="date/day")
    parser.add_argument("time", help="<hh:mm> (24hr)")
    parser.add_argument("duration", type=in_seconds,
            help="Num minutes clocked.")
    parser.add_argument("day_type",
                    choices=config.day_types, help="day-type")
    parser.add_argument("work_type",  choices=config.work_types,
            help="work-type")
    parser.add_argument("task",  help="task you are working on")
    parser.add_argument("--num-distractions", default=0,
            help="Number of distractions")
    parser.add_argument("--num-interruptions", default=0,
            help="Number of interruptions")
    parser.add_argument("--timezone", default=config.timezone,
            help="Your timezone")
    args = parser.parse_args(test_args)
    ts = date_time_utils.parse_date_time_to_ts(args.date, args.time,
            now_timestamp, args.timezone)
    db_table = db_module.create_record_table(config.db_full_path, logging_fn)
    db_table.insert(
            from_timestamp=ts, 
            to_timestamp = ts + args.duration,
            num_interruptions = args.num_interruptions,
            num_distractions = args.num_distractions,
            work_type = args.work_type,
            day_type = args.day_type,
            task = args.task
            )

    return (ts, db_table)

if __name__ == '__main__':
    from libworktracker import config as conf
    from libworktracker import record_db
    from libworktracker import io
    io_inst = io.InOut(print)
    config = conf.Config()
    main(config, record_db, io_inst.show_output, io_inst.log, time.time())
