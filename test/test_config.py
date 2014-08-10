from __future__ import print_function
import sys, os
# add our module dependencies to the path
deps_path = os.path.realpath(os.path.dirname(__file__) + "/..")
sys.path.append(deps_path)


import unittest
import tempfile
import time
import os
import shutil
import textwrap

from worktracker.libworktracker import config

class TestConfig(unittest.TestCase):
    def setUp(self):
        self.temp_dir = None
        self.temp_file = None

    def tearDown(self):
        if self.temp_dir:
            shutil.rmtree(self.temp_dir)
        if self.temp_file:
            os.remove(self.temp_file)

    def test10_verify_defaults(self):
        '''
        keep config_file_path None. Override data_dir to the temp dir.
        Check if the the file is created. Check if the values returned by
        config are right. Check if the values stored in the file are okay
        by creating another Config object from the file.
        '''
        self.temp_dir = tempfile.mkdtemp('test_config_dir')
        c1 = config.Config(overriding_params={'data_dir': self.temp_dir})
        self.assertEqual(c1.config_file_path, os.path.join(self.temp_dir,
            '.yattconfig'))
        self.assertEqual(c1.timeout_secs, 30*60)
        self.assertEqual(c1.day_types, ['work', 'holiday'])
        self.assertEqual(c1.work_types, ['project1', 'project2'])
        self.assertEqual(c1.min_work_block, 600)
        self.assertEqual(c1.timezone, 'Europe/London')
        #To check the values stored in the file lets reload it
        c2 = config.Config(file_path_from_cl=c1.config_file_path)
        self.assertEqual(c2.timeout_secs, 30*60)
        self.assertEqual(c2.day_types, ['work', 'holiday'])
        self.assertEqual(c2.work_types, ['project1', 'project2'])
        self.assertEqual(c2.min_work_block, 600)
        self.assertEqual(c2.timezone, 'Europe/London')
        self.assertEqual(c2.data_dir, self.temp_dir)

    def test20_verify_overrides(self):
        (_, self.temp_file) = tempfile.mkstemp('test_config_file')
        self.temp_dir = tempfile.mkdtemp('test_data_dir')
        o_params = {
                'data_dir': self.temp_dir,
                'timeout_secs': 42,
                'work_types': ["work1", 'work2'],
                'day_types': ['bad_day'],
                'min_work_block': 1,
                'timezone': 'Europe/London',
                'some_unknown_key': 'some_unknown_data'
                }
        c1 = config.Config(overriding_params=o_params,
                file_path_from_cl = self.temp_file)
        self.assertEqual(c1.timeout_secs, 42)
        self.assertEqual(c1.day_types, ['bad_day'])
        self.assertEqual(c1.work_types, ['work1', 'work2'])
        self.assertEqual(c1.min_work_block, 1)
        self.assertEqual(c1.timezone, 'Europe/London')
        self.assertEqual(c1.data_dir, self.temp_dir)
        #To check the values stored in the file lets reload it
        print(c1.config_file_path)
        print(self.temp_file)
        print(c1.data_dir)
        c2 = config.Config(file_path_from_cl=c1.config_file_path, 
                overriding_params={'timeout_secs':43})
        self.assertEqual(c2.timeout_secs, 43)
        self.assertEqual(c2.day_types, ['bad_day'])
        self.assertEqual(c2.work_types, ['work1', 'work2'])
        self.assertEqual(c2.min_work_block, 1)
        self.assertEqual(c2.timezone, 'Europe/London')
        self.assertEqual(c2.data_dir, self.temp_dir)

    def test30_verify_config_file(self):
        '''
        Creae a temp file. Write values to the temp file. Initialise
        Config with the temp file. Check values from config. Make sure
        that Config does not change the file.
        '''
        data = """
        [DEFAULT]
        data_dir = "/tmp/"
        min_work_block = 23
        day_types = ["bad_day", "good_day"]
        timeout_secs = 433
        timezone = "Anything"
        work_types = ["mars", "venus"]
        """
        (_, self.temp_file) = tempfile.mkstemp('test_config_file')
        self.temp_dir = tempfile.mkdtemp('test_data_dir')
        with open(self.temp_file, 'w') as f:
            f.write(textwrap.dedent(data))
        c1 = config.Config(file_path_from_cl=self.temp_file,
                overriding_params={'data_dir': self.temp_dir})
        self.assertEqual(c1.timeout_secs, 433)
        self.assertEqual(c1.day_types, ['bad_day', 'good_day'])
        self.assertEqual(c1.work_types, ['mars', 'venus'])
        self.assertEqual(c1.min_work_block, 23)
        self.assertEqual(c1.timezone, 'Anything')
        self.assertEqual(c1.data_dir, self.temp_dir)




if __name__ == '__main__':
    unittest.main()
