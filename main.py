from profiler import profiler, list_events
import pandas as pd
import numpy as np
import time, os

def list_all_events():
    print(list_events().get_supported_pmus())
    print(list_events().get_supported_events())

def from_pid(events, pid):
    perf= profiler(events_groups=events)
    perf.start_counters(pid)
    data= []
    while os.path.isdir('/proc/{}'.format(pid)):
        data.append(perf.read_events())
        time.sleep(0.1)
    return data

def workload(events):
    perf= profiler(program_args= ['./hello'], events_groups=events)
    data= perf.run(sample_period= 0.01, reset_on_sample=True)
    return data

def python_workload(events):
    perf= profiler(program_args= ['./hello'], events_groups=events)
    data= perf.run_python(sample_period= 0.01, reset_on_sample=True)
    return data

events= [['PERF_COUNT_HW_INSTRUCTIONS'], 
            ['PERF_COUNT_HW_CACHE_LL'], 
            ['PERF_COUNT_HW_BRANCH_INSTRUCTIONS'],
            ['PERF_COUNT_HW_BRANCH_MISSES'],
            ['PERF_COUNT_SW_PAGE_FAULTS']]
evs= list_events().get_supported_events()
rapl_evs= [ e for e in evs if 'RAPL' in e ]
rapl_evs= [['SYSTEMWIDE:'+e] for e in rapl_evs]
rapl_evs= [['PERF_COUNT_HW_INSTRUCTIONS']]+rapl_evs

try:
    # print(rapl_evs)
    # list_all_events()
    events+=rapl_evs
    data= workload(events)
    print("C++ ", len(data), np.sum(data,axis=0))
    data= python_workload(events)
    print("Python ", len(data), np.sum(data,axis=0))
    # data= from_pid(os.getppid(), rapl_evs)
except RuntimeError as e:
    print(e.args[0])