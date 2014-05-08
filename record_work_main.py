from __future__ import print_function
import argparse



def main(config, recorder_class, db_module, show_output_fn = print,
        logging_fn=print, test_args=None):
    '''
    config has configured default values as in config.py
    test_args can be used for testing when we don't want sys.argv
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument("work_type",  choices=config.work_types,
            help="work-type")
    parser.add_argument("day_type",
                    choices=config.day_types, help="day-type")
    parser.add_argument("--start-with", dest="start_with", type=int,
            help="start with number of minutes")
    parser.add_argument("--db-path", dest="db_path",
                default=config.db_full_path, help="Full path of the database")
    parser.add_argument("--timeout-secs", dest="timeout_secs", type=int,
                default=config.timeout_secs,
                help="Show progress and timeout after timeout seconds")
    args = parser.parse_args(test_args)
    db_table = db_module.create_record_table(config.db_full_path, logging_fn)
    # args contains the configured value optionally over-written by user
    recorder = recorder_class(args, db_table, show_output_fn, logging_fn)
    recorder.start()
    return (args, recorder, db_table)


if __name__ == '__main__':
    from config import Config
    from recorder import Recorder
    import record_db
    from io import InOut
    io_inst = InOut(print)
    io_inst.show_output('starting...')
    _, recorder,_ = main(Config, Recorder, record_db, io_inst.show_output,
            io_inst.log)
    io_inst.collect_input(recorder.handle_input)
    io_inst.show_output('quitting...')
