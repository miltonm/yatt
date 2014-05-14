from __future__ import print_function
import sys
sys.path.append('..')
import unittest
import tempfile
import os
import shutil
import time
import sqlite3

from worktracker.libworktracker import config as config_module

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
        self.test_args = "h yv".split() + ["test task"]
        self.temp_dir = tempfile.mkdtemp('test_recorder')

    def printfn(self, *args, **kwargs):
        show_gui_dialog = False
        to_play_sound = False
        if 'show_gui_dialog' in kwargs:
            show_gui_dialog = kwargs.pop('show_gui_dialog')
            print("show_gui_dialog:", show_gui_dialog)
        if 'play_sound' in kwargs:
            to_play_sound = kwargs.pop('play_sound')
            print("to_play_sound:", to_play_sound)
        print(*args, **kwargs)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_10_validate_args(self):
        from worktracker import record_now
        config = config_module.Config(overriding_params=
                {
                    'data_dir':self.temp_dir,
                    'day_types': ['w', 'h'],
                    'work_types': ['meta', 'yv', 'conpow']
                    })
        args, _, _ = record_now.main(config, MockRecorder,
                FakeDbModule,
                test_args = ['--start-with', '30', '--timeout-mins', '20',
                '--minimum-work-block', '10', 'h', 'meta', 'test task 10'],
                show_output_fn = self.printfn,
                logging_fn = self.printfn
                )
        self.assertEqual(args.work_type, 'meta')
        self.assertEqual(args.day_type, 'h')
        self.assertEqual(args.start_with, 30*60)
        self.assertEqual(args.timeout_secs, 20*60)
        self.assertEqual(args.min_work_block, 10*60)
        self.assertEqual(args.task, "test task 10")
        self.assertEqual(args.db_path, config.db_full_path)

    def test_20_verify_db_created_on_initialization(self):
        from worktracker import record_now
        from worktracker.libworktracker import record_db
        config = config_module.Config(overriding_params={
            'data_dir':self.temp_dir,
            'timeout_secs' : 1000,
            'day_types': ['w', 'h'],
            'work_types': ['meta', 'yv', 'conpow']
            })
        _, _, db_table = record_now.main(config, MockRecorder,
                record_db, test_args=self.test_args,
                show_output_fn = self.printfn,
                logging_fn = self.printfn)
        self.assertTrue(os.path.isfile(config.db_full_path))

    def test_30_verify_row_inserted_on_timeout(self):
        from worktracker import record_now
        from worktracker.libworktracker import record_db
        from worktracker.libworktracker import recorder
        # short timeout to check if the row has been inserted
        config_ob = config_module.Config(overriding_params={
            'data_dir':self.temp_dir,
            'timeout_secs' : 1,
            'min_work_block': 0,
            'day_types': ['w', 'h'],
            'work_types': ['meta', 'yv', 'conpow']
            })
        approx_from_time = time.time()
        _, recorder, db_table = record_now.main(config_ob,
                recorder.Recorder, record_db,
                test_args='h yv'.split() + ["test task 30"],
                show_output_fn = self.printfn,
                logging_fn = self.printfn
                )
        self.assertTrue(os.path.isfile(config_ob.db_full_path))
        time.sleep(2)
        conn = sqlite3.connect(config_ob.db_full_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM WorkRecord')
        r = cursor.fetchone()
        self.assertAlmostEqual(r['to_timestamp']-r['from_timestamp'], 1,
                delta=.5)
        self.assertAlmostEqual(r['from_timestamp'], approx_from_time,
                delta=.5)
        self.assertEqual(r['num_interruptions'], 0)
        self.assertEqual(r['num_distractions'], 0)
        self.assertEqual(r['work_type'], 'yv')
        self.assertEqual(r['day_type'], 'h')
        self.assertEqual(r['task'], 'test task 30')
        self.assertEqual(recorder.current_state, 'idle')

    def test_40_test_interrupt(self):
        from worktracker import record_now
        from worktracker.libworktracker import record_db
        from worktracker.libworktracker import recorder as r
        config = config_module.Config(overriding_params={
            'data_dir':self.temp_dir,
            'timeout_secs' : 600,
            'min_work_block': 0,
            'day_types': ['w', 'h'],
            'work_types': ['meta', 'yv', 'conpow']
            })
        approx_from_time = time.time()
        _, recorder, db_table = record_now.main(config,
                r.Recorder, record_db, test_args="h yv".split() + ["test 40"],
                show_output_fn = self.printfn,
                logging_fn = self.printfn)
        self.assertTrue(os.path.isfile(config.db_full_path))
        self.assertEqual(recorder.current_state, 'running')
        time.sleep(1)
        recorder.handle_input('i')
        conn = sqlite3.connect(config.db_full_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM WorkRecord')
        r = cursor.fetchone()
        self.assertAlmostEqual(r['to_timestamp']-r['from_timestamp'], 1,
                delta=.5)
        self.assertAlmostEqual(r['from_timestamp'], approx_from_time,
                delta=.5)
        self.assertEqual(r['num_interruptions'], 1)
        self.assertEqual(r['num_distractions'], 0)
        self.assertEqual(r['work_type'], 'yv')
        self.assertEqual(r['day_type'], 'h')
        self.assertEqual(r['task'], 'test 40')
        self.assertEqual(recorder.current_state, 'idle')

    def test_50_test_cancel(self):
        from worktracker import record_now
        from worktracker.libworktracker import record_db
        from worktracker.libworktracker import recorder as r
        config = config_module.Config(overriding_params={
            'data_dir':self.temp_dir,
            'timeout_secs' : 600,
            'min_work_block': 600 ,
            'day_types': ['w', 'h'],
            'work_types': ['meta', 'yv', 'conpow']
            })
        approx_from_time = time.time()
        _, recorder, db_table = record_now.main(config,
                r.Recorder, record_db, test_args="h yv".split()+['test 40'],
                show_output_fn = self.printfn,
                logging_fn = self.printfn)
        self.assertTrue(os.path.isfile(config.db_full_path))
        time.sleep(1)
        self.assertEqual(recorder.current_state, 'running')
        recorder.handle_input('c')
        conn = sqlite3.connect(config.db_full_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM WorkRecord')
        r = cursor.fetchall()
        self.assertEqual(len(r), 0)
        self.assertEqual(recorder.current_state, 'idle')

    def test_60_test_min_work_block(self):
        from worktracker import record_now
        from worktracker.libworktracker import record_db
        from worktracker.libworktracker import recorder as r
        config = config_module.Config(overriding_params={
            'data_dir':self.temp_dir,
            'timeout_secs' : 600,
            'min_work_block': 200,
            'day_types': ['w', 'h'],
            'work_types': ['meta', 'yv', 'conpow']
            })
        approx_from_time = time.time()
        _, recorder, db_table = record_now.main(config,
                r.Recorder, record_db, test_args="h yv".split()+["test 60"],
                show_output_fn = self.printfn,
                logging_fn = self.printfn)
        self.assertTrue(os.path.isfile(config.db_full_path))
        time.sleep(1)
        self.assertEqual(recorder.current_state, 'running')
        recorder.handle_input('i')
        conn = sqlite3.connect(config.db_full_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM WorkRecord')
        r = cursor.fetchall()
        self.assertEqual(len(r), 0)
        self.assertEqual(recorder.current_state, 'running')

    def test_70_test_distractions(self):
        from worktracker import record_now
        from worktracker.libworktracker import record_db
        from worktracker.libworktracker import recorder as r
        # short timeout to check if the row has been inserted
        config = config_module.Config(overriding_params={
            'data_dir':self.temp_dir,
            'timeout_secs' : 1,
            'min_work_block': 0,
            'day_types': ['w', 'h'],
            'work_types': ['meta', 'yv', 'conpow']
            })
        approx_from_time = time.time()
        _, recorder, db_table = record_now.main(config,
                r.Recorder, record_db, test_args="h yv".split()+['test 70'],
                show_output_fn = self.printfn,
                logging_fn = self.printfn)
        self.assertTrue(os.path.isfile(config.db_full_path))
        recorder.handle_input('d 3')
        recorder.handle_input('dis 2')
        recorder.handle_input('distraction 112')
        time.sleep(2)
        conn = sqlite3.connect(config.db_full_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM WorkRecord')
        r = cursor.fetchone()
        self.assertAlmostEqual(r['to_timestamp']-r['from_timestamp'], 1,
                delta=.5)
        self.assertAlmostEqual(r['from_timestamp'], approx_from_time,
                delta=.5)
        self.assertEqual(r['num_interruptions'], 0)
        self.assertEqual(r['num_distractions'], 117)
        self.assertEqual(r['work_type'], 'yv')
        self.assertEqual(r['day_type'], 'h')
        self.assertEqual(r['task'], 'test 70')
        self.assertEqual(recorder.current_state, 'idle')

    def test_80_test_task(self):
        from worktracker import record_now
        from worktracker.libworktracker import record_db
        from worktracker.libworktracker import recorder as r
        # short timeout to check if the row has been inserted
        config = config_module.Config(overriding_params={
            'data_dir':self.temp_dir,
            'timeout_secs' : 1,
            'min_work_block': 0,
            'day_types': ['w', 'h'],
            'work_types': ['meta', 'yv', 'conpow']
            })
        approx_from_time = time.time()
        _, recorder, db_table = record_now.main(config,
                r.Recorder, record_db, test_args="h yv".split()+['test 80 1'],
                show_output_fn = self.printfn,
                logging_fn = self.printfn)
        self.assertTrue(os.path.isfile(config.db_full_path))
        time.sleep(1.5)
        self.assertEqual(recorder.current_state, 'idle')
        # start again with a different task
        recorder.handle_input('s test 80 2')
        time.sleep(1.5)
        self.assertEqual(recorder.current_state, 'idle')
        # start again but with the same previous task
        recorder.handle_input('s')
        time.sleep(1.5)
        self.assertEqual(recorder.current_state, 'idle')
        conn = sqlite3.connect(config.db_full_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM WorkRecord')
        rows = cursor.fetchall()
        self.assertEqual(rows[-1]['task'], 'test 80 2')
        self.assertEqual(rows[-2]['task'], 'test 80 2')
        self.assertEqual(rows[-3]['task'], 'test 80 1')



if __name__ == '__main__':
    unittest.main()
