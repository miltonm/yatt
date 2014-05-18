from __future__ import print_function
import argparse

def main(config, db_module, record_retriever, io, args_list=None, parser=None):
    '''
    --average --total --per-day --detailed
    '''
    parser = parser or argparse.ArgumentParser()
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
    args = parser.parse_args(args_list)
    db_table = db_module.create_record_table(config.db_full_path, io.log)
    record_retriever.show_record(args, db_table, io)

if __name__=='__main__':
    from libworktracker import config as conf
    from libworktracker import record_db
    from libworktracker import io
    from libworktracker import record_retriever
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-path", dest="config_path",
                default=None, help="Path to the config file")
    (args, rest_of_args) = parser.parse_known_args()
    io_inst = io.InOut(print)
    config = conf.Config(file_path_from_cl=args.config_path,
            logging_fn=io_inst.log)
    main(config, record_db, record_retriever, io_inst, args_list=rest_of_args,
            parser=parser)
