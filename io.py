from __future__ import print_function
import sys
import threading

debug_mode = 10
#file_name = "/tmp/new_recorder.log"
#debug_mode = 0
file_name = None 


class InOut(object):
    def __init__(self, print_fn):
        self.waiting_for_input = False
        self._lock = threading.RLock()
        self.print_fn = print_fn

    def collect_input(self, handler):
        to_exit = False
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
        self.print_fn("---->", end=" ")
        sys.stdout.flush()

    def show_output(self, *args, **kwargs):
        with self._lock:
            self.print_fn('')
            self.print_fn(file=sys.stdout, *args, **kwargs)
            if self.waiting_for_input:
                self.show_prompt()

    def log(self, priority , msg):
        if priority <= debug_mode:
            self.show_output("recorder-log: ", msg)
        if file_name:
            with open(file_name, 'a') as f:
                self.print_fn(msg, file=f)
