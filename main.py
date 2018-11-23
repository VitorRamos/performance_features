from profiler import profiler, list_events
import pandas as pd
import numpy as np
import time, os

def list_all_events():
    print(list_events().get_supported_pmus())
    print(list_events().get_supported_events())

def from_pid(events):
    perf= profiler(events_groups=events)
    perf.start_counters(os.getpid())
    for i in range(100):
        print(perf.read_events())
        time.sleep(0.1)

def workload(events):
    perf= profiler(program_args= ['./hello'], events_groups=events)
    data= perf.run(sample_period= 0.01, reset_on_sample=False)
    print(data)

def python_workload(events):
    perf= profiler(program_args= ['./hello'], events_groups=events)
    data= perf.run_python(sample_period= 0.01, reset_on_sample=False)
    print(data)

events= [['PERF_COUNT_HW_INSTRUCTIONS'], 
            ['PERF_COUNT_HW_CACHE_LL'], 
            ['PERF_COUNT_HW_BRANCH_INSTRUCTIONS'],
            ['PERF_COUNT_HW_BRANCH_MISSES'],
            ['PERF_COUNT_SW_PAGE_FAULTS']]

try:
    evs= list_events().get_supported_events()
    rapl_evs= [ e for e in evs if 'RAPL' in e ]

    rapl_evs= [['SYSTEMWIDE:'+e] for e in rapl_evs]
    rapl_evs= [['PERF_COUNT_HW_INSTRUCTIONS']]+rapl_evs
    print(rapl_evs)
    # list_all_events()
    # workload(events)
    # python_workload(events)
    from_pid(rapl_evs)
except RuntimeError as e:
    print(e.args[0])