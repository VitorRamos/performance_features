# Performance Counters api for python

[![Build Status](https://travis-ci.com/VitorRamos/performance_features.svg?branch=master)](https://travis-ci.com/VitorRamos/performance_features)


## Table of contents

- [What are the performance counters](#whatis)
- [The API](#api)
- [Installation](#install)
- [Example usage](#usage)

<a name="whatis"/>

## What are the performance counters
Performance counters are special hardware registers available on most modern CPUs. These registers count the number of certain types of events: such as instructions executed, cache misses suffered, or branches mis-predicted without slowing down the kernel or applications. These registers can also trigger interrupts when a threshold number of events have passed and can thus be used to profile the code that runs on that CPU.

## Reading Performance counters
+ **Instructions**
  + **rdmsr**: Reads the contents of a 64-bit model specific register (MSR) specified in the ECX register into registers EDX:EAX. This instruction must be executed at privilege level 0 or in real-address mode

  + **rdpmc**: Is slightly faster that the equivelent rdmsr instruction. rdpmc can also be configured to allow access to the counters from userspace, without being priviledged.
+ **From Userspace** (Linux) : The Linux Performance Counter subsystem provides an abstraction of these hardware capabilities. It provides per task and per CPU counters, counter groups, and it provides event capabilities on top of those. It provides "virtual" 64-bit counters, regardless of the width of the underlying hardware counters. Performance counters are accessed via special file descriptors. There's one file descriptor per virtual counter used. The special file descriptor is opened via the perf_event_open() system call. These system call do not use rdpmc but rdpmc is not necessarily faster than other methods for reading event values.

<a name="api"/>

## Python API
This module provide a high-level abstraction API to Linux perf events without overhead while executing

## How it works:
Using perfmon library python wrapper to perform the system calls and configure the structures to create the file descriptors.

The file descriptors are passed to the workload module develop on c++ which start the target application and read from the file descriptors

<a name="install"/>

## Installation (Only Ubuntu 18.04)
```bash
sudo apt install python3-pip python3-dev swig libpfm4-dev
pip3 install performance-features
```

## Installation from the source
```
git clone https://github.com/VitorRamos/performance_features.git
cd performance_features
./install.sh
```

<a name="usage"/>

## Usage

### List events
```python
from profiler import *

print(get_supported_pmus())
print(get_supported_events())
```

### Sampling events
```python
from profiler import *

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