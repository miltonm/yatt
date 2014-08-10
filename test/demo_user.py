#!/usr/bin/env python
'''
It creates a demo config and a demo database in /tmp. The script will populate
the database with example data and will output the path to the config (which
will contain the full path to the corresponding sqlite db). You can use other
tools to play with the config and pre-populated db. When done, invoke the
script with '--clean' option when the database and the config file will be
cleaned.
'''
from __future__ import print_function
import sys
sys.path.append('..')
import argparse
import os
import tempfile
import shutil
import time
import random
from worktracker import record_past
from worktracker.libworktracker import record_db
from worktracker.libworktracker import config
from worktracker.libworktracker import date_time_utils


def cleanse(args):
    shutil.rmtree(os.path.dirname(args.config_path))

def create_config():
    temp_dir = tempfile.mkdtemp('demo_dir')
    o_params = {
            'data_dir': temp_dir,
            'timeout_secs': 42,
            'work_types': ["work1", 'work2'],
            'day_types': ['bad_day', 'good_day'],
            'min_work_block': 1,
            'timezone': 'Europe/London',
            }
    c1 = config.Config(overriding_params=o_params)
    return c1

def last_n_eods(n, tz):
    (start_of_today, _ ) = date_time_utils.parse_date_to_ts_range(
            "today", time.time(), tz)
    eoy = start_of_today - 1
    day_in_secs = 24*60*60
    return xrange(eoy - n*day_in_secs + 1, eoy, day_in_secs)

def sample_ts_dur(eod, x):
    day_in_secs = 24*60*60
    # get 10 sample time stamps in the day at least 30 mins apart
    samples = random.sample(range(eod - day_in_secs + 1, eod, 30*60), x)
    samples = sorted(samples)
    # create tuples of sample timestamps and duration bet. the sample and the
    # next one
    for i in xrange(x - 1):
        yield (samples[i], samples[i+1] - samples[i])
    
def add_to_db(ts1, ts2, conf, db_table):
    db_table.insert(
            from_timestamp=ts1, 
            to_timestamp=ts2,
            num_interruptions=random.randrange(0,5),
            num_distractions=random.randrange(0,20),
            work_type=random.choice(conf.work_types),
            day_type=random.choice(conf.day_types),
            task="at the moment we only have test tasks" 
            )

def populate(args):
    conf = (config.Config(file_path_from_cl=args.config_path) 
            if args.config_path
            else create_config())
    print(conf.config_file_path)
    db_table = record_db.create_record_table(conf.db_full_path, print)
    # prepopulate data for last 5 weeks
    for eod in last_n_eods(35, conf.timezone):
        for (ts, diff) in sample_ts_dur(eod, 10):
            add_to_db(ts, random.randrange(ts, ts+diff), conf, db_table)
    # get iterator giving end_of_day timestamps for last 35 days
    # for each end_of_day timestamp get 10 sample in-day-timestamps
    # for each in-day-timestamp choose duration ( unsolved )

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    parser_populate = subparsers.add_parser('populate')
    parser_populate.add_argument("--config-path", dest="config_path",
                 default=None, help="Path to the config file")
    parser_populate.set_defaults(func=populate)
    #
    parser_cleanse = subparsers.add_parser('cleanse')
    parser_cleanse.add_argument("config_path")
    parser_cleanse.set_defaults(func=cleanse)
    args = parser.parse_args()
    args.func(args)
