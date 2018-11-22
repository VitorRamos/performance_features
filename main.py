import workload, os
import time, struct
import perfmon

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

class event_group:
    def __init__(self, pname, events, group=False):
        self.system = perfmon.System()
        self.event_names = events
        self.events = []
        self.fds = []
        self.group= group
        self.program= workload.Workload(workload.stringVec(pname))
        for e in events:
            err, encoding = perfmon.pfm_get_perf_event_encoding(e, perfmon.PFM_PLM0 | perfmon.PFM_PLM3, None, None)
            self.events.append(encoding)

    def create_fds(self):
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
            
                self.fds.append(perfmon.perf_event_open(e, self.program.pid, -1, -1, 0))

    def reset(self):
        pass

    def enable(self):
        pass

    def disable(self):
        pass

    def read(self):
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

    def go1(self):
        self.program.start()
        while self.program.isAlive:
            data= self.read()
            print(data)
            time.sleep(0.01)
        data= self.read()
        print(data)
        
    def go2(self):
        if self.group:
            aux= workload.intVec([self.fds[0]])
            self.program.add_event(aux)
        else:
            self.program.add_event(workload.intVec(self.fds))
        data= self.program.run(False, 1e4)
        print(data)
        for v in data:
            print(v)

try:
    perf= event_group(['./hello'], ['PERF_COUNT_HW_INSTRUCTIONS', 'PERF_COUNT_HW_CACHE_LL', 
                                    'PERF_COUNT_HW_BRANCH_INSTRUCTIONS','PERF_COUNT_HW_BRANCH_MISSES'], False)
    perf.create_fds()
    perf.go1()
except RuntimeError as e:
    print(e.args[0])