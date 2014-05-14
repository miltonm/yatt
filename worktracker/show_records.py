from __future__ import print_function
import argparse

def main(config, db_module, record_retriever, io, test_args=None):
    '''
    --average --total --per-day --detailed
    '''
    parser = argparse.ArgumentParser()
    when_group = parser.add_mutually_exclusive_group(required=True)
    when_group.add_argument('--oneday', 
            help="Stats for one day. Format: today/yesterday/<dd-mm-yyyy>")
    when_group.add_argument('--range', nargs=2, dest='trange', 
            metavar = ('<start-date>', '<end-date>'),
            help='''Format: today/yesterday/<dd-mm-yyyy>.
            Example: --range 24-05-2014 26-06-2014''')
    when_group.add_argument('--last', nargs=2,
            metavar = ('<number>', '<days/weeks/months>'),
            help=" Example: '--last 1 month', '--last 20 days'")
    parser.add_argument("--timezone", default=config.timezone,
            help="Your timezone")
    args = parser.parse_args(test_args)
    print(args)
    db_table = db_module.create_record_table(config.db_full_path, io.log)
    record_retriever.show_record(args, db_table, io)

if __name__=='__main__':
    from libworktracker import config as conf
    from libworktracker import record_db
    from libworktracker import io
    from libworktracker import record_retriever
    io_inst = io.InOut(print)
    config = conf.Config()
    main(config, record_db, record_retriever, io_inst)
