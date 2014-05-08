from __future__ import print_function
import threading
import time
from functools import partial


class RecorderStateMachine(object):
    '''
    This should really be private inner class of Recorder.
    It mainly consists of the state machine table :
    Table = { 
            <source-state-1> : {  
            <action-done>: (< handler_to_be_called, <destination-state>),
            <action>: (<handler>, <state>
            }
            <source-state-2> : {}
    '''
    STATE_TABLE = {
            'idle': {
                'start': ('_start_handler', 'running'),
                'quit':('_do_nothing', 'idle')
                },
            'running': {
                'quit': ('_interrupt_handler', 'idle'),
                'interrupt': ('_interrupt_handler', 'idle'),
                'cancel':('_cancel_handler', 'idle'),
                'timeout':('_timeout_handler', 'idle'),
                }
            }
    def __init__(self, recorder):
        self.recorder = recorder

    def act(self, action, *args, **kwargs):
        cs = self.recorder.current_state
        table = RecorderStateMachine.STATE_TABLE
        # when things go wrong we generate an error message
        if cs not in table or action not in table[cs]:
            self.recorder.show_output("The action:%s does not do anything"
                    " in the current state: %s"%(action, cs))
            return False
        try:
            handler_name = table[cs][action][0]
            is_success = getattr(self.recorder, handler_name)(*args, **kwargs)
            if is_success:
                self.recorder.current_state = table[cs][action][1]
            return is_success
        except Exception as e:
            self.recorder.log(1, "Exception thrown while handling"
                    " action(%s)"%(action))
            self.recorder.log(1, e)
        return False



class Recorder(object):
    def __init__(self, config, db_table, show_output, logging_fn):
        self.show_output = show_output
        self.log = logging_fn
        self.config = config
        self.table = db_table
        self.start_time = None
        self.end_time = None
        self.num_distractions = 0
        self._lock = threading.Lock()
        self.wdone_timer = None
        self.current_state = 'idle'
        self.state_machine = RecorderStateMachine(self)
        self.last_duration = 0
        self.last_task = config.task

    def get_prompt_text(self):
        return self.current_state.upper()

    def _record_work_done(self, was_interrupted = False, end_time=None):
        if not end_time:
            end_time = time.time()
        self.end_time = end_time
        self.table.insert(from_timestamp=self.start_time, 
                to_timestamp = self.end_time,
                num_interruptions = int(was_interrupted),
                num_distractions = self.num_distractions,
                work_type = self.config.work_type,
                day_type = self.config.day_type,
                task = self.last_task
                )
        self.last_duration = self.end_time - self.start_time
        # to ensure we don't do duplicate
        self.end_time = 0
        self.start_time = 0
        return self.last_duration

    def _cancel_handler(self):
        with self._lock:
            self.last_duration = time.time() - self.start_time
            self.wdone_timer.cancel()
            self.end_time = 0
            self.start_time = 0
            self.num_distractions = 0
        return True

    def _timeout_handler(self):
        with self._lock:
            self.wdone_timer.cancel()
            self._record_work_done()
            self.num_distractions = 0
        return True

    def _timeout_cb(self):
        is_success = self.state_machine.act('timeout')
        if is_success:
            self.show_output("Work timeout after %s mins. Use s(start)"
                    " to start a new block of work."%(self.last_duration/60.0),
                    show_gui_dialog=True, play_sound=True)

    def _start_handler(self, args=None):
        with self._lock:
            if args:
                task = " ".join(args)
                task = task.strip()
                if task: 
                    self.last_task = task
            self.num_distractions = 0
            self.start_time = time.time()
            self.wdone_timer = threading.Timer(self.config.timeout_secs,
                    self._timeout_cb)
            self.wdone_timer.start()
        self.log(2, "getting out of start_handler")
        return True

    def _interrupt_handler(self):
        with self._lock:
            if not self.wdone_timer.is_alive():
                self.log(2, "Interrupted but no timer running !!!")
            self.wdone_timer.cancel()
            end_time = time.time()
            diff = end_time - self.start_time
            if diff < self.config.min_work_block:
                min_w_b = self.config.min_work_block/60.0
                self.show_output("Sorry cannot record work as you worked for"
                        " %s minutes which is less than the minimum work block."
                        " Minimum work block is %s mins. You can now work "
                        "till you have worked for at least %s minutes or "
                        "'cancel' current work block."%((diff/60.0), min_w_b,
                            min_w_b))
                return False
            self._record_work_done(was_interrupted = True)
            self.num_distractions = 0
            return True

    def _do_nothing(self):
        return True

    def start(self):
        self.state_machine.act('start')

    def _distraction_hanlder(self, arg_list):
        retval = [True, 0, ""]
        try:
            if arg_list:
                d_num_str = arg_list[0]
                self.num_distractions += int(d_num_str)
            else:
                self.num_distractions += 1
            retval[1] = self.num_distractions
        except (TypeError, ValueError) as e:
            retval = (False, self.num_distractions, str(e))
        return retval

    def handle_input(self, input_str):
        ''' returns True if it wants to exit '''
        #import pdb;pdb.set_trace()
        current_state_was = self.current_state
        num_distractions = self.num_distractions
        input_strs = input_str.split()
        if not input_strs:
            return False
        elif 'quit'.startswith(input_strs[0]):
            # 'quit' is 'save and quit'
            is_success = self.state_machine.act('quit')
            if is_success and current_state_was == "running":
                self.show_output("Logged %s mins of work. You were dstrctd"
                        " %s number of times."%(
                    self.last_duration/60.0, num_distractions))
            return True
        elif'cancel'.startswith(input_strs[0]):
            is_success = self.state_machine.act('cancel')
            if is_success and current_state_was == "running":
                self.show_output("Cancelled %s mins of work"%(
                    self.last_duration/60.0))
        elif 'interrupt'.startswith(input_strs[0]):
           is_success = self.state_machine.act('interrupt')
           if is_success and current_state_was == "running":
               self.show_output("Interrupted after %s mins. You had %s"
                       " dstrctns"%(self.last_duration/60.0,
                           num_distractions))
        elif 'start'.startswith(input_strs[0]):
           is_success = self.state_machine.act('start', input_strs[1:])
           if is_success and current_state_was != 'running':
               self.show_output("Started logging time")
        elif 'distractions'.startswith(input_strs[0]):
           # this one does not affect statemachine
            is_success, num, msg = self._distraction_hanlder(input_strs[1:])
            if is_success:
                self.show_output("Num dstrctns so far: ", num)
            else:
                self.show_output("Something went wrong.", msg)
        else:
            self.show_output("Unrecognised Command")
        return False

