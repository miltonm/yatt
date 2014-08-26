#!/usr/bin/env python
from __future__ import print_function
import argparse
from libworktracker import date_time_utils as dutil
from libworktracker import lib_goals
import time

#todo
# - change set_goal to goals
# change all parsers to have parent parsers
# refactor all initial parsing stuff to keep them in a function

def set_goal(goal):
    goal.set_goal()

def show_goals(goal):
    goal.show_goals()

def main(config, db_module, record_retriever, io, now_ts, args_list=None,
        parser=None):
    ''' main for set_goal '''
    parser = argparse.ArgumentParser(parents=[parser] if parser else [])
    subparsers = parser.add_subparsers()
    parser_set = subparsers.add_parser('set')
    parser_set.add_argument("name", help="Name of the goal")
    parser_set.add_argument("work_type",  choices=config.work_types,
            help="work-type for the goal")
    parser_set.add_argument("num_hours", type=int,
            help="hours you want to put in")
    parser_set.add_argument("start_date",
            help="when you want to start as <dd-mm-yyyy>")
    parser_set.add_argument("end_date",
            help="you want to do these hours by this date in <dd-mm-yyyy>")
    parser_set.set_defaults(func=set_goal)
    parser_show = subparsers.add_parser('show')
    parser_show.set_defaults(func=show_goals)
    args = parser.parse_args()
    goal = lib_goals.Goal(config, db_module, io, now_ts, args)
    args.func(goal)

if __name__ == '__main__':
    from libworktracker import config as conf
    from libworktracker import record_db
    from libworktracker import io
    from libworktracker import record_retriever
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--config-path", dest="config_path",
                default=None, help="Path to the config file")
    parser.add_argument("--log-dir", dest="log_dir",
                default=None, help="Path to the dir where you want to keep "
                " the log file")
    (args, rest_of_args) = parser.parse_known_args()
    io_inst = io.InOut(print, log_dir=args.log_dir)
    config = conf.Config(file_path_from_cl=args.config_path,
            logging_fn=io_inst.log)
    main(config, record_db, record_retriever, io_inst, time.time(),
            args_list=rest_of_args, parser=parser)
    # goal set <name> <work_type> <num-hours> <start-date> <end-date>
    # goals set conpow 100 14-08-2014 14-10-2014
    # goals show
    # For each goal
    # Name of goal, when it was started
    # Number of days before end-date
    # Number of hours left to reach the goal
    # Expected number of hours per week to get there

