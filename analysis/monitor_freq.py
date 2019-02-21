from profiler import Profiler, get_event_description
from tqdm import tqdm
import pandas as pd
import numpy as np
import os, pickle, time

flat_list= lambda x: [ g for f in x for g in f ]
double_list= lambda x: [[g] for g in x]
split_n= lambda x, n: [x[i:i + n] for i in range(0, len(x), n)]

def run_program(pargs, to_monitor, n=30, sample_period=0.05, reset_on_sample= False, list_threads=[1], idle_time=10):
    """
        Run the program multiple times
    """
    from cpufreq import cpuFreq
    cpu= cpuFreq()
    cpu.reset()
    time.sleep(idle_time)
    cpu.disable_hyperthread()
    cpu.set_governors("userspace")
    freqs = cpu.get_available_frequencies()
    cpus = cpu.get_online_cpus()

    all_data= []
    
    try:
        for thr in list_threads:
            cpu.reset()
            time.sleep(idle_time)
            cpu.disable_hyperthread()
            cpu.set_governors("userspace")
            cpu.disable_cpu(cpus[thr:])
            info_freqs = []
            for f in freqs:
                cpu.set_frequencies(f)
                counters= []
                for i in range(n):
                    print("{} : {} threads, {} freq, {} run".format(pargs,thr,f,i))
                    program= Profiler(program_args=pargs, events_groups=to_monitor)
                    data= program.run(sample_period=sample_period,reset_on_sample=reset_on_sample)
                    counters.append(data)
                
                l1= {"freq": f, "data":counters}
                info_freqs.append(l1.copy())
            
            l2= {"thr": thr, "threads":info_freqs}
            all_data.append(l2.copy())
    except RuntimeError as e:
        print(e.args[0])
    except Exception as e:
        print("Error", e)

    try:
        print("Reseting the cpus...")
        cpu.reset()
        cpu.set_governors("ondemand")
    except:
        print("Cant reset the cpus")

    data= {'n':n, 'sample_period':sample_period,'reset_on_sample':reset_on_sample, 'data':all_data, 'to_monitor':to_monitor}
    
    return data


def run_polybench(to_monitor):
    falta= set(os.listdir('polybench'))-set( [f.replace('_freq.dat','') for f in os.listdir('.') if 'freq' in f] )
    for f in falta:
        #if 'EXTRALARGE' in f: continue
        pdir= 'polybench/'+f
        if os.path.isdir(pdir): continue
        n= 15
        reset_on_sample= False
        sample_period= 0.05

        data= run_program(pargs=[pdir],to_monitor=to_monitor,n=n,reset_on_sample=reset_on_sample,sample_period=sample_period,
        list_threads=[4])

        with open('{}_freq.dat'.format(f),'wb+') as f:
            pickle.dump(data, f)

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