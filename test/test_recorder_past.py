from __future__ import print_function
import sys
sys.path.append('..')
import unittest
import datetime
import calendar
import time
import pytz
import sqlite3
import tempfile
import shutil
import os

from worktracker.libworktracker import config as config_module
from worktracker.libworktracker import date_time_utils

class MockDb(object):
    pass

class TestRecorderPast(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp('test_recorder')

    def tearDown(self):
        shutil.rmtree(self.temp_dir)


    def test_10_check_db(self):
        from worktracker import record_past
        from worktracker.libworktracker import record_db
        config = config_module.Config(overriding_params={
            'data_dir': self.temp_dir,
            'timezone':'Europe/London',
            'day_types': ['w', 'h'],
            'work_types': ['meta', 'yv', 'conpow']
            })
        ts, table = record_past.main(config,
                record_db, print, print, time.time(),
                args_list = '--num-distractions 42 --num-interruptions 42 '
                'today 21:00 30 w conpow'.split() + ["test task 40"]
                )
        self.assertTrue(os.path.isfile(config.db_full_path))
        conn = sqlite3.connect(config.db_full_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM WorkRecord')
        r = cursor.fetchone()
        self.assertEqual(r['to_timestamp']-r['from_timestamp'], 30*60)
        self.assertEqual(r['from_timestamp'], ts)
        self.assertEqual(r['num_interruptions'], 42)
        self.assertEqual(r['num_distractions'], 42)
        self.assertEqual(r['work_type'], 'conpow')
        self.assertEqual(r['day_type'], 'w')
        self.assertEqual(r['task'], 'test task 40')


if __name__ == '__main__':
    unittest.main()
