from datetime import datetime
import os

def get_default_db_name():
    current_year = datetime.now().year
    return str(current_year)+'-recorder.db'

def get_default_dir():
    return os.getcwd()

def get_db_full_path():
    return os.path.join(get_default_dir(), get_default_db_name())

class Config(object):
    timeout_secs = 30*60
    day_types = ['w', 'h']
    work_types = ['conpow', 'yv', 'meta']
    db_full_path = get_db_full_path()
    
