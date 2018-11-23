from . import workload
import perfmon
import time, struct, os, signal, fcntl

class profiler:
    PERF_EVENT_IOC_ENABLE = 0x2400
    PERF_EVENT_IOC_DISABLE = 0x2401
    PERF_EVENT_IOC_ID = 0x80082407
    PERF_EVENT_IOC_RESET = 0x2403

    def __init__(self, program_args, events_groups):
        self.chceck_paranoid()
        self.system = perfmon.System()
        self.event_groups_names = events_groups
        self.event_groups = []
        self.fd_groups = []
        self.pname= program_args
        self.program= None
        self.encode_events()

    def chceck_paranoid(self):
        with open('/proc/sys/kernel/perf_event_paranoid', 'r') as f:
            val= int(f.read())
            if val != -1:
                raise Exception("Paranoid enable")

    def encode_events(self):
        for group in self.event_groups_names:
            ev_list= []
            for e in group:
                #TODO check err
                err, encoding = perfmon.pfm_get_perf_event_encoding(e, perfmon.PFM_PLM0 | perfmon.PFM_PLM3, None, None)
                ev_list.append(encoding)
            self.event_groups.append(ev_list)

    def create_events(self):
        #TODO check is program exists and fd erros
        for group in self.event_groups:
            fd_list= []
            if len(group) > 1:
                e= group[0]
                e.exclude_kernel = 1
                e.exclude_hv = 1
                e.inherit= 1
                e.disable= 1
                e.read_format= perfmon.PERF_FORMAT_GROUP  | perfmon.PERF_FORMAT_TOTAL_TIME_ENABLED
                fd= perfmon.perf_event_open(e, self.program.pid, -1, -1, 0)
                if fd < 1: raise Exception("Error creating fd")
                fd_list.append(fd)
                for e in group[1:]:
                    e.exclude_kernel = 1
                    e.exclude_hv = 1
                    e.inherit= 1
                    e.disable= 1
                    e.read_format= perfmon.PERF_FORMAT_GROUP  | perfmon.PERF_FORMAT_TOTAL_TIME_ENABLED
                    fd= perfmon.perf_event_open(e, self.program.pid, -1, fd_list[0], 0)
                    if fd < 1: raise Exception("Error creating fd")
                    fd_list.append(fd)
            else:
                for e in group:
                    e.exclude_kernel = 1
                    e.exclude_hv = 1
                    e.inherit= 1
                    e.disable= 1

                    fd= perfmon.perf_event_open(e, self.program.pid, -1, -1, 0)
                    if fd < 0: raise Exception("Erro creating fd")
                    fd_list.append(fd)
            self.fd_groups.append(fd_list)
    
    def destroy_events(self):
        for group in self.fd_groups:
            for fd in group:
                os.close(fd)
        self.fd_groups= []

    def kill_program(self):
        if self.program and self.program.isAlive:
            print("Killing process", self.program.pid)
            self.program.start()
            os.kill(self.program.pid, signal.SIGKILL)

    def enable_events(self):
        for fd in self.fd_groups:
            fcntl.ioctl(fd[0], profiler.PERF_EVENT_IOC_ENABLE, 0)

    def disable_events(self):
        for fd in self.fd_groups:
            fcntl.ioctl(fd[0], profiler.PERF_EVENT_IOC_DISABLE, 0)

    def reset_events(self):
        for fd in self.fd_groups:
            fcntl.ioctl(fd[0], profiler.PERF_EVENT_IOC_RESET, 0)

    def read_events(self):
        data= []
        for group in self.fd_groups:
            raw= os.read(group[0], 4096)
            to_read= int(len(raw)/8)
            raw= struct.unpack('q'*to_read ,raw)
            data+=raw
        return data

    def initialize(self):
        try:
            self.destroy_events()
            self.kill_program()
            self.program= workload.Workload(workload.stringVec(self.pname))
            self.program.MAX_SIZE_GROUP= 30
            self.create_events()
            for group in self.fd_groups:
                self.program.add_events(workload.intVec([group[0]]))
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

        return self.format_data(data)
        
    def go2(self, period):
        self.initialize()
        data= self.program.run(True, period*1e6)
        aux= []
        for v in data:
            aux.append(list(v))
        
        return self.format_data(data)
    
    def format_data(self, data):
        all_data= []
        for s in data:
            only_s= []
            s= list(s)
            c= 0
            for g in self.event_groups_names:
                if len(g) > 1:
                    only_s+=s[c+2:c+2+len(g)]
                    c=c+2+len(g)
                else:
                    only_s+=[s[c]]
                    c+=1
            all_data.append(only_s)
        return all_data