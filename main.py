from profiler import profiler
import pandas as pd
import numpy as np

try:
    events= [['PERF_COUNT_HW_INSTRUCTIONS'], 
            ['PERF_COUNT_HW_CACHE_LL'], 
            ['PERF_COUNT_HW_BRANCH_INSTRUCTIONS','PERF_COUNT_HW_BRANCH_MISSES'],
            ['PERF_COUNT_SW_PAGE_FAULTS']]
           
    perf= profiler(program_args= ['./hello'], events_groups=events)
    data= perf.run(period= 0.01)
    flat_list = [item for sublist in events for item in sublist]
    df= pd.DataFrame(data, columns= flat_list)
    print(df)
    
except RuntimeError as e:
    print(e.args[0])