import unittest
from profiler import Profiler
import os, time

def is_process_running(process_id):
    try:
        os.kill(process_id, 0)
        return True
    except OSError:
        return False


def run_n(n):
    def ntime(of):
        def func(*args, **kargs):
            for i in range(n-1):
                of(*args, **kargs)
            return of(*args, **kargs)
        return func
    return ntime

class TestCompareMethods(unittest.TestCase):
    pass
class TestProfilerMethods(unittest.TestCase):

    @run_n(1)
    def test_run(self):
        for sp in [-0.1, 0, 0.1]:
            for res in [True, False]:
                program= Profiler(program_args=['./hello'], events_groups=[['PERF_COUNT_HW_INSTRUCTIONS']])
                self.assertTrue(program.run(sample_period=sp, reset_on_sample=res))
        
        for sp in [-0.1, 0, 0.1]:
            for res in [True, False]:
                with self.assertRaises(Exception):
                    program= Profiler(program_args=['./hello'], events_groups=[['INVALID']])
                    program.run(sample_period=sp, reset_on_sample=res)
                
                with self.assertRaises(Exception):
                    program= Profiler(program_args=['INVALID'], events_groups=[['PERF_COUNT_HW_INSTRUCTIONS']])
                    program.run(sample_period=sp, reset_on_sample=res)
                
                with self.assertRaises(Exception):
                    program= Profiler(program_args=['INVALID'], events_groups=[['INVALID']])
                    program.run(sample_period=sp, reset_on_sample=res)

    @run_n(10)
    def test_runpython(self):
        for sp in [-0.1, 0, 0.1]:
            for res in [True, False]:
                program= Profiler(program_args=['./hello'], events_groups=[['PERF_COUNT_HW_INSTRUCTIONS']])
                self.assertTrue(program.run_python(sample_period=sp, reset_on_sample=res))
        
        for sp in [-0.1, 0, 0.1]:
            for res in [True, False]:
                with self.assertRaises(Exception):
                    program= Profiler(program_args=['./hello'], events_groups=[['INVALID']])
                    program.run_python(sample_period=sp, reset_on_sample=res)
                
                with self.assertRaises(Exception):
                    program= Profiler(program_args=['INVALID'], events_groups=[['PERF_COUNT_HW_INSTRUCTIONS']])
                    program.run_python(sample_period=sp, reset_on_sample=res)
                
                with self.assertRaises(Exception):
                    program= Profiler(program_args=['INVALID'], events_groups=[['INVALID']])
                    program.run_python(sample_period=sp, reset_on_sample=res)

    @run_n(10)
    def test_runbackground(self):
        # BUG when run run_background too fast and chield dosent exit
        # waitpid never recived initial signal to start ptrace
        # some other race conditions can happen to

        for sp in [-0.1, 0, 0.1]:
            for res in [True, False]:
                program= Profiler(program_args=['./hello'], events_groups=[['PERF_COUNT_HW_INSTRUCTIONS']])
                program.run_background()
                while program.program.isAlive: pass
        
        for sp in [-0.1, 0, 0.1]:
            for res in [True, False]:
                with self.assertRaises(Exception):
                    program= Profiler(program_args=['./hello'], events_groups=[['INVALID']])
                    program.run_background()
                    while program.program.isAlive: pass
                
                with self.assertRaises(Exception):
                    program= Profiler(program_args=['INVALID'], events_groups=[['PERF_COUNT_HW_INSTRUCTIONS']])
                    program.run_background()
                    while program.program.isAlive: pass
                
                with self.assertRaises(Exception):
                    program= Profiler(program_args=['INVALID'], events_groups=[['INVALID']])
                    program.run_background()
                    while program.program.isAlive: pass

import os, time
if __name__ == '__main__':
    unittest.main()
