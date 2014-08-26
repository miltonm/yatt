from __future__ import print_function
import sys
import threading
import os
import subprocess
import textwrap
from thirdparty import texttable
import inspect
import time

import date_time_utils

#debug_mode = 10
file_name = os.path.join(os.getcwd(), "debuglog")
debug_mode = 0
#file_name = None 



class InOut(object):
    fmt = '%Y-%m-%d %H:%M:%S %Z%z'
    def get_date_time_str(self):
        ts = time.time()
        local_dt = date_time_utils.ts_to_local_datetime(ts, "Europe/London")
        dt_output_str = local_dt.strftime(self.fmt)
        return dt_output_str
        
    def __init__(self, print_fn, log_dir=None, get_user_input_fn=raw_input):
        self.log_dir = log_dir
        self.waiting_for_input = False
        self._lock = threading.RLock()
        self.print_fn = print_fn
        self.get_user_input = get_user_input_fn
        self.asset_path = self.get_asset_path()
        self.get_prompt_text = None

    def get_asset_path(self):
        module_dir = os.path.dirname(inspect.getabsfile(self.__class__))
        asset_dir = os.path.join(module_dir, '..', '..', 'assets')
        if not os.path.exists(asset_dir):
            self.log(1, "Can not find asset dir")
            return
        asset_file_path = os.path.join(asset_dir, 'CallRingingOut.wav')
        if not os.path.isfile(asset_file_path):
            self.log(1, "Cannot find the asset file")
        self.log(2, "asset_file_path: %s"%(asset_file_path))
        return asset_file_path

    def set_prompt_text_fn(self, prompt_text_fn):
        self.get_prompt_text = prompt_text_fn

    def collect_input(self, handler):
        to_exit = False
        self.show_prompt()
        while not to_exit:
            self.waiting_for_input = True
            s = raw_input(' ')
            s = s.strip()
            if s:
                to_exit = handler(s)
            else:
                self.show_output('')
        self.waiting_for_input = False

    def show_error(self, *args, **kwargs):
        self.print_fn(file=sys.stderr, *args, **kwargs)

    def show_prompt(self):
        prompt_text = ''
        if self.get_prompt_text:
            prompt_text = self.get_prompt_text()
        self.print_fn("(%s)"%(prompt_text) + "---->", end=" ")
        sys.stdout.flush()

    def run_on_system(self, command_and_args):
        try:
            output = subprocess.check_output(
                    command_and_args,
                    stderr=subprocess.STDOUT)
            self.log(2, output)
        except subprocess.CalledProcessError as e:
            self.log(2, "Exception in os command: %s"%(command_and_args))
            self.log(2, str(e))

    def show_gui_dialog(self, *args, **kwargs):
        all_str = " ".join(args)
        if 'linux' in os.sys.platform:
            self.run_on_system(['notify-send', '-u', 'critical', '-t', '0',
                all_str])

    def play_sound_on_thread(self):
        threading.Thread(target=self.play_sound).start()

    def play_sound(self):
        if 'linux' in os.sys.platform:
            for _ in xrange(1):
                self.run_on_system(['play', self.asset_path, 'vol',
                    '10', 'dB'])

    def show_output(self, *args, **kwargs):
        with self._lock:
            show_gui_dialog = False
            to_play_sound = False
            if 'show_gui_dialog' in kwargs:
                show_gui_dialog = kwargs.pop('show_gui_dialog')
            if 'play_sound' in kwargs:
                to_play_sound = kwargs.pop('play_sound')
            self.print_fn('')
            self.print_fn(file=sys.stdout, *args, **kwargs)
            if self.waiting_for_input:
                self.show_prompt()
            if show_gui_dialog:
                self.show_gui_dialog(*args, **kwargs)
            if to_play_sound:
                self.play_sound()

    def log(self, priority , msg):
        if priority <= debug_mode:
            self.show_output("recorder-log: ", msg)
        if self.log_dir:
            msg = "%s :: %s"%(self.get_date_time_str(), msg)
            logfile_path = os.path.join(self.log_dir, 'debuglog')
            with open(logfile_path, 'a') as f:
                self.print_fn(msg, file=f)

    def show_table(self, headers, data_dict_list, max_width=80):
        table = texttable.Texttable(max_width=max_width)
        table.add_row(headers)
        for d in data_dict_list:
            r = []
            for name in headers:
                content = textwrap.fill(d[name], 20)
                r.append(content)
            table.add_row(r)
        self.print_fn(table.draw())

    def get_confirmation(self, question, failure_text=None, success_text=None):
        user_input = self.get_user_input(question)
        if not 'yessssss'.startswith(user_input.lower()):
            if failure_text:
                self.show_output(failure_text)
            return False
        if success_text:
            self.show_output(success_text)
        return True

