from profiler import *
from tqdm import tqdm
import os
import pandas as pd
import numpy as np
import pickle

flat_list= lambda x: [ g for f in x for g in f ]
double_list= lambda x: [[g] for g in x]
split_n= lambda x, n: [x[i:i + n] for i in range(0, len(x), n)]

def run_program(pargs, to_monitor, n=30, sample_period=0.05, reset_on_sample= False):
    """
        Run the program multiple times
    """
    try:
        all_data= []
        for i in range(n):
            program= Profiler(program_args=pargs, events_groups=to_monitor)
            data= program.run(sample_period=sample_period,reset_on_sample=reset_on_sample)
            all_data.append(data)
    except RuntimeError as e:
        print(e.args[0])
    return all_data

# Interrest
all_events= get_event_description()
rapl_events=['SYSTEMWIDE:'+e[0] for e in all_events if 'RAPL' in e[0]]
hw_events= [['PERF_COUNT_HW_INSTRUCTIONS','PERF_COUNT_HW_BRANCH_INSTRUCTIONS', 'PERF_COUNT_HW_BRANCH_MISSES', 'PERF_COUNT_HW_CACHE_MISSES']]
mem_events= [['PERF_COUNT_HW_INSTRUCTIONS','MEM_UOPS_RETIRED:ALL_LOADS', 'MEM_UOPS_RETIRED:ALL_STORES','FP_COMP_OPS_EXE:X87']]
sw_events= [['PERF_COUNT_SW_CPU_CLOCK','PERF_COUNT_SW_PAGE_FAULTS','PERF_COUNT_SW_CONTEXT_SWITCHES',
                       'PERF_COUNT_SW_CPU_MIGRATIONS','PERF_COUNT_SW_PAGE_FAULTS_MAJ']]
rapl_events= double_list(rapl_events)
to_monitor= hw_events+sw_events+rapl_events

for f in tqdm(os.listdir('polybench')):
    pdir= 'polybench/'+f
    if os.path.isdir(pdir): continue
    n= 15
    reset_on_sample= False
    sample_period= 0.05
    data= run_program(pargs=[pdir],to_monitor=to_monitor,n=n,reset_on_sample=reset_on_sample,sample_period=sample_period)
    to_save= {'n':n, 'sample_period':sample_period,'reset_on_sample':reset_on_sample, 'data':data, 'to_monitor':to_monitor}
    with open('{}.dat'.format(f),'wb+') as f:
        pickle.dump(to_save, f)

to_monitor= mem_events+sw_events+rapl_events

for f in tqdm(os.listdir('polybench')):
    pdir= 'polybench/'+f
    if os.path.isdir(pdir): continue
    n= 15
    reset_on_sample= False
    sample_period= 0.05
    data= run_program(pargs=[pdir],to_monitor=to_monitor,n=n,reset_on_sample=reset_on_sample,sample_period=sample_period)
    to_save= {'n':n, 'sample_period':sample_period,'reset_on_sample':reset_on_sample, 'data':data, 'to_monitor':to_monitor}
    with open('{}_mem.dat'.format(f),'wb+') as f:
        pickle.dump(to_save, f)

# with open('gemm_SMALL_DATASET.dat', 'rb+') as f:
#     data= pickle.load(f)
#     print(data)