# Performance Counters api for python

A high-level abstraction API for Linux perf events with low overhead

[![Continuous Integration](https://github.com/VitorRamos/performance_features/actions/workflows/main.yml/badge.svg)](https://github.com/VitorRamos/performance_features/actions/workflows/main.yml)

## Table of contents

- [Installation](#install)
- [Example usage](#usage)
- [How it works](#whatis)


<a name="install"/>

## Install from pip
```bash
sudo apt install g++ gcc swig libpfm4-dev python3-dev python3-pip
pip install performance-features
```

## Install from source
```bash
git clone https://github.com/VitorRamos/performance_features.git
cd performance_features
sudo ./install.sh
```

<a name="usage"/>

## Usage

### List events
```python
from performance_features import *

print(get_supported_pmus())
print(get_supported_events())
```

### Sampling events
```python
from performance_features import *

try:
    events= [['PERF_COUNT_HW_INSTRUCTIONS'],
            ['PERF_COUNT_HW_BRANCH_INSTRUCTIONS','PERF_COUNT_HW_BRANCH_MISSES'],
            ['PERF_COUNT_SW_PAGE_FAULTS']]
    perf= Profiler(program_args= ['/bin/ls','/'], events_groups=events)
    data= perf.run(sample_period= 0.01)
    print(data)
except RuntimeError as e:
    print(e.args[0])
```

<a name="whatis"/>

## How it works:

A c module create a workload using Linux ptrace to ensure we control the starting the application and collect the events data with minimal overhead. The events are setup using the perf_event_open syscall through the perfmom library.

## What are the performance counters
Performance counters are special hardware registers available on most modern CPUs. These registers count the number of certain types of events: such as instructions executed, cache misses suffered, or branches mis-predicted without slowing down the kernel or applications. These registers can also trigger interrupts when a threshold number of events have passed and can thus be used to profile the code that runs on that CPU.

## Reading Performance counters
+ **Instructions**
  + **rdmsr**: Reads the contents of a 64-bit model specific register (MSR) specified in the ECX register into registers EDX:EAX. This instruction must be executed at privilege level 0 or in real-address mode

  + **rdpmc**: Is slightly faster that the equivelent rdmsr instruction. rdpmc can also be configured to allow access to the counters from userspace, without being priviledged.
+ **From Userspace** (Linux) : The Linux Performance Counter subsystem provides an abstraction of these hardware capabilities. It provides per task and per CPU counters, counter groups, and it provides event capabilities on top of those. It provides "virtual" 64-bit counters, regardless of the width of the underlying hardware counters. Performance counters are accessed via special file descriptors. There's one file descriptor per virtual counter used. The special file descriptor is opened via the perf_event_open() system call. These system call do not use rdpmc but rdpmc is not necessarily faster than other methods for reading event values.
