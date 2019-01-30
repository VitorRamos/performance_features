from profiler import Profiler, run_program, get_event_description
from tqdm import tqdm
import pandas as pd
import numpy as np
import os, pickle

flat_list= lambda x: [ g for f in x for g in f ]
double_list= lambda x: [[g] for g in x]
split_n= lambda x, n: [x[i:i + n] for i in range(0, len(x), n)]

def run_polybench(to_monitor):
    falta= set(os.listdir('polybench'))-set( [f.replace('_mem.dat','') for f in os.listdir('.') if 'mem' in f] )
    for f in tqdm(falta):
        #if 'EXTRALARGE' in f: continue
        pdir= 'polybench/'+f
        if os.path.isdir(pdir): continue
        n= 15
        reset_on_sample= False
        sample_period= 0.05
        data= run_program(pargs=[pdir],to_monitor=to_monitor,n=n,reset_on_sample=reset_on_sample,sample_period=sample_period)
        to_save= {'n':n, 'sample_period':sample_period,'reset_on_sample':reset_on_sample, 'data':data, 'to_monitor':to_monitor}
        with open('{}_mem.dat'.format(f),'wb+') as f:
            pickle.dump(to_save, f)

# Interrest
all_events= get_event_description()
rapl_events=['SYSTEMWIDE:'+e[0] for e in all_events if 'RAPL' in e[0]]
hw_events= [['PERF_COUNT_HW_INSTRUCTIONS','PERF_COUNT_HW_BRANCH_INSTRUCTIONS', 'PERF_COUNT_HW_BRANCH_MISSES', 'PERF_COUNT_HW_CACHE_MISSES']]
# FP_COMP_OPS_EXE:X87 ARITH:DIVIDER_UOPS FP_ARITH_INST_RETIRED:SCALAR
mem_events= [['PERF_COUNT_HW_INSTRUCTIONS','MEM_UOPS_RETIRED:ALL_LOADS', 'MEM_UOPS_RETIRED:ALL_STORES','FP_COMP_OPS_EXE:X87']]
sw_events= [['PERF_COUNT_SW_CPU_CLOCK','PERF_COUNT_SW_PAGE_FAULTS','PERF_COUNT_SW_CONTEXT_SWITCHES',
                       'PERF_COUNT_SW_CPU_MIGRATIONS','PERF_COUNT_SW_PAGE_FAULTS_MAJ']]
rapl_events= double_list(rapl_events)

to_monitor= mem_events+sw_events+rapl_events
run_polybench(to_monitor)
# to_monitor= hw_events+sw_events+rapl_events
# run_polybench(to_monitor)