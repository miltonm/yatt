from __future__ import print_function
import unittest
import tempfile
import os
import shutil
import time
import sqlite3

import record_work_main
from dp import dp
import config

class FakeDbModule(object):
    @staticmethod
    def create_record_table(*args, **kwargs):
        pass

class MockRecorder(object):
    def __init__(self, *args, **kwargs):
        pass
    def start(self):
        pass

class TestRecorder(unittest.TestCase):

    def setUp(self):
        self.test_args = "yv h".split()
        self.temp_dir = tempfile.mkdtemp('test_recorder')
        self.db_path = os.path.join(self.temp_dir,
                config.get_default_db_name())

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_10_validate_args(self):
        from config import Config
        args, _, _ = record_work_main.main(Config, MockRecorder, FakeDbModule,
                test_args = "meta h --start-with 30".split())
        self.assertEqual(args.work_type, 'meta')
        self.assertEqual(args.day_type, 'h')
        self.assertEqual(args.start_with, 30)
        self.assertEqual(args.db_path, Config.db_full_path)

    def test_20_verify_db_created_on_initialization(self):
        import record_work
        import record_db
        # Long timeout
        config.Config.timeout_secs = 1000 
        config.Config.db_full_path = self.db_path
        _, _, db_table = record_work_main.main(config.Config, MockRecorder,
                record_db, test_args=self.test_args)
        self.assertTrue(os.path.isfile(config.Config.db_full_path))

    def test_30_verify_row_inserted_on_timeout(self):
        import record_work
        import record_db
        from recorder import Recorder
        # short timeout to check if the row has been inserted
        config.Config.timeout_secs = 1
        config.Config.db_full_path = self.db_path
        approx_from_time = time.time()
        _, _, db_table = record_work_main.main(config.Config, Recorder,
                record_db, test_args="yv h".split())
        self.assertTrue(os.path.isfile(config.Config.db_full_path))
        time.sleep(2)
        conn = sqlite3.connect(config.Config.db_full_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM WorkRecord')
        r = cursor.fetchone()
        self.assertAlmostEqual(r['to_timestamp']-r['from_timestamp'], 1,
                delta=1)
        self.assertAlmostEqual(r['from_timestamp'], approx_from_time,
                delta=2)
        self.assertEqual(r['num_interrupts'], 0)
        self.assertEqual(r['num_distractions'], 0)
        self.assertEqual(r['work_type'], 'yv')
        self.assertEqual(r['day_type'], 'h')

    def test_40_verify_state_changes_on_actions(self):
        pass



if __name__ == '__main__':
    unittest.main()
