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
            'idle': {'start': ('_start_handler', 'running')},
            'interrupted': {
                'resume': ('_resume_handler', 'running'), 
                            'cancel':('_cancel_handler', 'idle')
                            },
            'running': {
                'interrupt': ('_interrupt_handler', 'interrupted'),
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
            self.recorder.show_error(1, "Not a valid action(%s) in the current"
                    "state(%s)"%(action, cs))
            return False
        try:
            handler_name = table[cs][action][0]
            getattr(self.recorder, handler_name)(*args, **kwargs)
            self.recorder.current_state = table[cs][action][1]
            return True
        except Exception as e:
            self.recorder.show_error(1, "Exception thrown while handling"
                    " action(%s)"%(action))
            self.recorder.show_error(1, e)
        return False



class Recorder(object):
    def __init__(self, config, db_table, show_output, show_error):
        self.show_output = show_output
        self.show_error = show_error
        self.config = config
        self.table = db_table
        self.start_time = None
        self.end_time = None
        self.num_interrupts = 0
        self.num_distractions = 0
        self._lock = threading.Lock()
        self.wdone_timer = None
        self.current_state = 'idle'
        self.state_machine = RecorderStateMachine(self)

    def _verify_change_state(self, action):
        # this does not allow rollback
        # todo : turn it into a context manager
        try:
            self.current_state = self.state_table[self.current_state][action]
            return True
        except KeyError:
            self.show_error(1, 'Not a valid action(%s) in current state(%s)',
                    action, self.current_state)

    def _log_in_db(self):
        self.table.insert(from_timestamp=self.start_time, 
                to_timestamp = self.end_time,
                num_interrupts = self.num_interrupts,
                num_distractions = self.num_distractions,
                work_type = self.config.work_type,
                day_type = self.config.day_type
                )

    def _timeout_handler(self):
        with self._lock:
            self.end_time = time.time()
            self._log_in_db()

    def _start_handler(self):
        self.start_time = time.time()
        self.wdone_timer = threading.Timer(self.config.timeout_secs,
                partial(self.state_machine.act, 'timeout'))
        self.wdone_timer.start()

    def _interrupt_handler(self):
        self.wdone_timer.cancel()
        if wdone_timer.is_alive():
            with self._lock:
                self.end_time = time.time()
                self._log_in_db()
        else:
            raise Exception("Interrupted but no timer running !!!")

    def start(self):
        self.state_machine.act('start')

    def handle_input(self, input_str):
        ''' returns True if it wants to exit '''
        with self._lock:
            input_strs = input_str.split()
            if not input_strs:
                return False
            elif 'quit'.startswith(input_strs[0]):
                # 'quit' is 'save and quit'
                self.state_machine.act('interrupt')
                return True
            elif'cancel'.startswith(input_strs[0]):
                self.state_machine.act('cancel')
            elif 'interrupt'.startswith(input_strs[0]):
               self.state_machine.act('interrupt')
            elif 'resume'.startswith(input_strs[0]):
               self.state_machine.act('resume')
            elif 'distractions'.startswith(input_strs[0]):
               # this one does not affect statemachine
                self._distraction_hanlder(input_strs[1:])
            return False

