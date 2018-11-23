import workload
import perfmon
import time, struct, os, signal, fcntl

class list_events:
    def __init__(self):
        self.system= perfmon.System()

    def get_supported_pmus(self):
        pmus= []
        for pmu in self.system.pmus:
            pmu_info= pmu.info
            if pmu_info.flags.is_present:
                pmus.append(pmu_info.name)
        return pmus

    def get_supported_events(self, name=''):
        evs= []
        for pmu in self.system.pmus:
            pmu_info= pmu.info
            if pmu_info.flags.is_present:
                for event in pmu.events():
                    if name in event.info.name:
                        evs.append(event)
        return evs

class profiler:
    PERF_EVENT_IOC_ENABLE = 0x2400
    PERF_EVENT_IOC_DISABLE = 0x2401
    PERF_EVENT_IOC_ID = 0x80082407
    PERF_EVENT_IOC_RESET = 0x2403

    def __init__(self, program_args, events_names, group=False):
        self.chceck_paranoid()
        self.system = perfmon.System()
        self.event_names = events_names
        self.events = []
        self.fds = []
        self.group= group
        self.pname= program_args
        self.program= None
        self.encode_events()

    def chceck_paranoid(self):
        with open('/proc/sys/kernel/perf_event_paranoid', 'r') as f:
            val= int(f.read())
            if val != -1:
                raise Exception("Paranoid enable")

    def encode_events(self):
        for e in self.event_names:
            #TODO check err
            err, encoding = perfmon.pfm_get_perf_event_encoding(e, perfmon.PFM_PLM0 | perfmon.PFM_PLM3, None, None)
            self.events.append(encoding)

    def create_events(self):
        #TODO check is program exists
        if self.group:
            e= self.events[0]
            e.exclude_kernel = 1
            e.exclude_hv = 1
            e.inherit= 1
            e.disable= 1
            e.read_format= perfmon.PERF_FORMAT_GROUP | perfmon.PERF_FORMAT_ID | perfmon.PERF_FORMAT_TOTAL_TIME_ENABLED | perfmon.PERF_FORMAT_TOTAL_TIME_RUNNING
            self.fds.append(perfmon.perf_event_open(e, self.program.pid, -1, -1, 0))
            for e in self.events[1:]:
                e.exclude_kernel = 1
                e.exclude_hv = 1
                e.inherit= 1
                e.disable= 1
                e.read_format= perfmon.PERF_FORMAT_GROUP | perfmon.PERF_FORMAT_ID | perfmon.PERF_FORMAT_TOTAL_TIME_ENABLED | perfmon.PERF_FORMAT_TOTAL_TIME_RUNNING
                self.fds.append(perfmon.perf_event_open(e, self.program.pid, -1, self.fds[0], 0))

        else:
            for e in self.events:
                e.exclude_kernel = 1
                e.exclude_hv = 1
                e.inherit= 1
                e.disable= 1

                fd= perfmon.perf_event_open(e, self.program.pid, -1, -1, 0)
                if fd < 0:
                    raise Exception("Erro creating fd")
                self.fds.append(fd)
    
    def destroy_events(self):
        for fd in self.fds:
            os.close(fd)
        self.fds= []

    def kill_program(self):
        if self.program and self.program.isAlive:
            print("Killing process", self.program.pid)
            self.program.start()
            os.kill(self.program.pid, signal.SIGKILL)

    def enable_events(self):
        if self.group:
            fcntl.ioctl(self.fds[0], profiler.PERF_EVENT_IOC_ENABLE, perfmon.PERF_IOC_FLAG_GROUP)
        else:
            for fd in self.fds:
                fcntl.ioctl(fd, profiler.PERF_EVENT_IOC_ENABLE, 0)

    def disable_events(self):
        if self.group:
            fcntl.ioctl(self.fds[0], profiler.PERF_EVENT_IOC_DISABLE, perfmon.PERF_IOC_FLAG_GROUP)
        else:
            for fd in self.fds:
                fcntl.ioctl(fd, profiler.PERF_EVENT_IOC_DISABLE, 0)

    def reset_events(self):
        if self.group:
            fcntl.ioctl(self.fds[0], profiler.PERF_EVENT_IOC_RESET, perfmon.PERF_IOC_FLAG_GROUP)
        else:
            for fd in self.fds:
                fcntl.ioctl(fd, profiler.PERF_EVENT_IOC_RESET, 0)

    def read_events(self):
        data= []
        if self.group:
            aux= os.read(self.fds[0], 4096)
            to_read= int(len(aux)/8)
            aux= struct.unpack('q'*to_read ,aux)
            for i in range( int((to_read-3)/2) ):
                data.append(aux[ int(i*2+3) ])
        else:
            for fd in self.fds:
                aux= os.read(fd, 8)
                aux= struct.unpack('q' ,aux)[0]
                data.append(aux)
        return data

    def initialize(self):
        try:
            self.destroy_events()
            self.kill_program()
            self.program= workload.Workload(workload.stringVec(self.pname))
            self.create_events()
            if self.group:
                self.program.add_events(workload.intVec([self.fds[0]]))
            else:
                self.program.add_events(workload.intVec(self.fds))
        except:
            self.kill_program()
            raise

    def go1(self, period):
        self.initialize()
        self.program.start()
        data= []
        while self.program.isAlive:
            time.sleep(period)
            data.append(self.read_events())
            self.reset_events()
        data.append(self.read_events())
        return data
        
    def go2(self, period):
        self.initialize()
        data= self.program.run(True, period*1e6)
        aux= []
        for v in data:
            if self.group:
                aux.append(list(v)[3::2])
            else:
                aux.append(list(v))
        return aux

import numpy as np

try:
    perf= profiler(['./hello'], ['PERF_COUNT_HW_INSTRUCTIONS', 'PERF_COUNT_HW_CACHE_LL', 
                                    'PERF_COUNT_HW_BRANCH_INSTRUCTIONS','PERF_COUNT_HW_BRANCH_MISSES'], True)
    data= perf.go1(0.01)
    print(np.sum(data,axis=0), len(data))
    data= perf.go2(0.01)
    print(np.sum(data,axis=0), len(data))
except RuntimeError as e:
    print(e.args[0])