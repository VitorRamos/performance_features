#!/bin/bash

# disable paranoid (all users can read perf events)
sysctl -w kernel.perf_event_paranoid=-1
# disable nmi watchdog (more PMC's left)
sysctl -w kernel.nmi_watchdog=0

# change frequency permition
sudo chmod -R 777 /sys/devices/system/cpu/cpu*/cpufreq/
sudo chmod -R 777 /sys/devices/system/cpu/cpu*/online
sudo modprobe msr
