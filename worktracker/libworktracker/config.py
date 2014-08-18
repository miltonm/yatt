'''
Look for ~~/.config/yatt/.yattconfig if not there generate one.
Default dir the db file would be ~/.config/yatt/.yattconfig
but this can be configured to reside somewhere else by setting the 
value of 'data_dir'.

Config file can be specified from command line. 

'''
from __future__ import print_function
from datetime import datetime
import os
from ConfigParser import SafeConfigParser
import json

import misc_utils



class Config(object):
    def __init__(self, file_path_from_cl=None, overriding_params=None,
            logging_fn=print):
        '''
        Impl logic:
        If there is no file: 'overriding_params' take precedance over
        default vals.
        If a config file is there: 'overriding_params' should take precedance
        over both file read values and default values.
        The resultant config should be written to config on instantiation.

        file_path_from_cl: file path entered from command line
        '''
        # Though config_parser is going to be defined later it's hard
        # to debug any attribute access error till that point as in
        # __getattr__ calls _get_from_conf which tries to access config_parser
        # on self and any non-attribute access would create an infinite loop.
        # With self.config_parser defined as 'None', we will get something
        # more predictable when we try to access a non-exitent attribue.
        self.config_parser = None
        self.log = logging_fn
        over_vals = overriding_params or {}
        default_vals = {
                'timeout_secs': 30*60,
                'day_types': ['work', 'holiday'],
                'work_types': ['project1', 'project2'],
                'min_work_block': 10*60,
                'timezone': 'Europe/London'
                }
        default_vals['data_dir'] = os.path.join(os.path.expanduser('~'),
                '.config', 'yatt')
        # self.default_vals.update(over_vals)
        data_dir = over_vals.get('data_dir', default_vals['data_dir'])
        (self.config_file_path, file_tobe_created) = self._get_config_file(
                file_path_from_cl, data_dir)
        # jsonify the dicts
        jsonify_vals = lambda d:dict(
                [(k, json.dumps(v)) for (k,v) in d.items()])
        default_vals = jsonify_vals(default_vals) 
        over_vals = jsonify_vals(over_vals) 
        self.config_parser= self._get_config(
                self.config_file_path,
                default_vals,
                over_vals,
                file_tobe_created)
        # we have to use data dir from config parser
        # note: db_full_path cannot be configured only the dir can be
        # configured.
        data_dir = self._get_from_conf('data_dir')
        self.db_full_path = os.path.join(data_dir, self.get_default_db_name())
        # make sure data_dir exists
        misc_utils.mkdir_p(data_dir)
        self.log(2, "DB path: %s"%(self.db_full_path))
        self.log(2, "config path: %s"%(self.config_file_path))

    def get_default_db_name(self):
        current_year = datetime.now().year
        return str(current_year)+'-recorder.db'

    def _get_config_file(self, file_path, data_dir):
        file_tobe_created = False
        if not file_path:
            file_path = os.path.join(data_dir,'.yattconfig')
        if not os.path.isfile(file_path):
            file_tobe_created = True
            # here we make sure parent dirs are there
            misc_utils.mkdir_p(os.path.dirname(file_path))
        return (file_path, file_tobe_created)

    def _write_intro(self, f):
        print('; For string values use double quotes. For example:', file=f)
        print('; timezone = "Europe/London"', file=f)
        print('; day_types and work_types are lists of strings:', file=f)
        print('; day_types = ["holiday", "work-day"]', file=f)
        print('; work_types = ["project-1", "project-2"]', file=f)
        print('; Dont use double quotes for integers:', file=f)
        print('; min_work_block = 600', file=f)
        print('; More generally values are all json formatted.', file=f)

    def _get_config(self, file_path, default_vals, over_vals,
            file_tobe_created):
        '''
        - open existing config
        - overwrite default dict with overriding values
        '''
        config_parser = SafeConfigParser(default_vals)
        if not file_tobe_created:
            config_parser.read(file_path)
        # Now rewrite params that are there in over_vals
        for p in over_vals:
            config_parser.set('DEFAULT', p, over_vals[p])
        with open(file_path, 'w') as f:
            self._write_intro(f)
            config_parser.write(f)
        return config_parser

    def _get_from_conf(self, conf_name):
        return json.loads(self.config_parser.get('DEFAULT', conf_name))

    def __getattr__(self, name):
        #import pdb; pdb.set_trace()
        f = object.__getattribute__(self, '_get_from_conf')
        return f(name)




