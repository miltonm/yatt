from __future__ import print_function
import sys
import threading
import os
import subprocess
import textwrap
from thirdparty import texttable

#debug_mode = 10
file_name = os.path.join(os.getcwd(), "debuglog")
debug_mode = 0
#file_name = None 


class InOut(object):
    def __init__(self, print_fn):
        self.waiting_for_input = False
        self._lock = threading.RLock()
        self.print_fn = print_fn
        self.get_prompt_text = None

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
        except CalledProcessError as e:
            self.log(2, "Exception in notify-send")
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
                self.run_on_system(['play', 'assets/CallRingingOut.wav', 'vol',
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
        if file_name:
            with open(file_name, 'a') as f:
                self.print_fn(msg, file=f)

    def show_table(self, headers, data_dict_list):
        table = texttable.Texttable()
        table.add_row(headers)
        for d in data_dict_list:
            r = []
            for name in headers:
                content = textwrap.fill(d[name], 20)
                r.append(content)
            table.add_row(r)
        self.print_fn(table.draw())

