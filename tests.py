import unittest
from profiler import Profiler

class TestProfilerMethods(unittest.TestCase):

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

    def test_runbackground(self):
        # BUG when run run_background too fast and chield dosent exit
        # waitpid never recived initial signal to start ptrace
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
    

    # def test_upper(self):
    #     self.assertEqual('foo'.upper(), 'FOO')
    #     self.assertTrue('FOO'.isupper())
    #     self.assertFalse('Foo'.isupper())

if __name__ == '__main__':
    unittest.main()