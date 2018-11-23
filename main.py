from profiler import profiler, events
import numpy as np

try:
    perf= profiler(['./hello'], [['PERF_COUNT_HW_INSTRUCTIONS'], ['PERF_COUNT_HW_CACHE_LL'], 
                                    ['PERF_COUNT_HW_BRANCH_INSTRUCTIONS','PERF_COUNT_HW_BRANCH_MISSES'],['PERF_COUNT_SW_PAGE_FAULTS']])
    data= perf.go1(0.01)
    print(np.sum(data,axis=0), len(data))
    data= perf.go2(0.01)
    print(np.sum(data,axis=0), len(data))
except RuntimeError as e:
    print(e.args[0])