from __future__ import print_function
import argparse
import sys

def do_nothing(*args, **kwargs):
    pass

def main(config, recorder_class, db_module, show_output_fn = do_nothing,
        logging_fn=do_nothing, test_args=None):
    '''
    config has configured default values.
    test_args can be used for testing when we don't want sys.argv.
    '''
    def in_seconds(arg_val):
        arg_val_min = float(arg_val)
        return int(arg_val_min*60)

    parser = argparse.ArgumentParser()
    parser.add_argument("day_type",
                    choices=config.day_types, help="day-type")
    parser.add_argument("work_type",  choices=config.work_types,
            help="work-type")
    parser.add_argument("task",  help="task you are working on")
    parser.add_argument("--start-with", dest="start_with", type=in_seconds,
            help="start with number of minutes (not supported yet)")
    parser.add_argument("--db-path", dest="db_path",
                default=config.db_full_path, help="Full path of the database")
    parser.add_argument("--timeout-mins", dest="timeout_secs", 
                type=in_seconds,
                default=config.timeout_secs,
                help="Show progress and timeout after timeout minutes")
    parser.add_argument("--minimum-work-block", dest="min_work_block",
            type=in_seconds, default=config.min_work_block,
            help="Work is not recorded if interrupted before you work for"
            " at least these many minutes")
    args = parser.parse_args(test_args)
    if args.min_work_block > args.timeout_secs:
        show_output_fn("Minimum work block cannot be more than the timeout."
                "Your minimum work block is set to %s and your timeout is"
                " set to %s. Please modify your configuration or command line"
                " parameters to correct it."%(args.min_work_block/60.0, 
                    args.timeout_secs/60.0)
                )
        return (False, False, False)
    db_table = db_module.create_record_table(config.db_full_path, logging_fn)
    # args contains the configured value optionally over-written by user
    recorder = recorder_class(args, db_table, show_output_fn, logging_fn)
    recorder.start()
    return (args, recorder, db_table)


if __name__ == '__main__':
    from libworktracker import config as conf
    from libworktracker import recorder as r
    from libworktracker import record_db
    from libworktracker import io
    io_inst = io.InOut(print)
    config = conf.Config(logging_fn=io_inst.log)
    _, recorder,_ = main(config, r.Recorder, record_db, io_inst.show_output,
            io_inst.log)
    if not recorder:
        sys.exit(1)
    io_inst.set_prompt_text_fn(recorder.get_prompt_text)
    io_inst.collect_input(recorder.handle_input)
