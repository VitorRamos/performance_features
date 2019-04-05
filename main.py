from profiler import Profiler, get_supported_events
import pandas as pd
import numpy as np

flat_list= lambda x: [ g for f in x for g in f ]
double_list= lambda x: [[g] for g in x]
split_n= lambda x, n: [x[i:i + n] for i in range(0, len(x), n)]

try:
    evs= get_supported_events()
    software_events= [e for e in evs if 'PERF_COUNT_SW' in e]
    hardware_events= [e for e in evs if 'PERF_COUNT_HW' in e]
    hw_groups= split_n(hardware_events, 10)
    evs_monitor= hw_groups[0:1]+[software_events]
<<<<<<< HEAD
=======
    evs_monitor= [['PERF_COUNT_HW_INSTRUCTIONS']]
>>>>>>> ebb6e8c2d115f0d9359bf193bff504f4a578fc63
    
    program= Profiler(program_args=['./hello'], events_groups=evs_monitor)
    data= program.run(sample_period=0.01,reset_on_sample=False)
    df= pd.DataFrame(data, columns= flat_list(evs_monitor) )
    print(df)
except RuntimeError as e:
    print(e.args[0])