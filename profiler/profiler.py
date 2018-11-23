"""
    This module provie a high level api to linux perf events witout overhead while executing

    How it works:
        Using perfmon python wrapper to the system calls and structures the file descriptors are created
        The file descriptors are passed to the workload module develop on c++ wich start the target application and sample the file descriptors
    
"""

from . import workload
import perfmon
import time, struct, os, signal, fcntl

class profiler:
    PERF_EVENT_IOC_ENABLE = 0x2400
    PERF_EVENT_IOC_DISABLE = 0x2401
    PERF_EVENT_IOC_ID = 0x80082407
    PERF_EVENT_IOC_RESET = 0x2403

    def __init__(self, program_args, events_groups):
        """
            program_args : list with program name and arguments to run
            events_groups : list of list of event names, each list is a event group with event leader the first name
        """
        self.chceck_paranoid()
        self.system = perfmon.System()
        self.event_groups_names = events_groups
        self.event_groups = []
        self.fd_groups = []
        self.program_args= program_args
        self.program= None
        self.encode_events()

    def chceck_paranoid(self):
        """
        Check perf_event_paranoid wich Controls use of the performance events 
        system by unprivileged users (without CAP_SYS_ADMIN).
        The default value is 2.

        -1: Allow use of (almost) all events by all users
            Ignore mlock limit after perf_event_mlock_kb without CAP_IPC_LOCK
        >=0: Disallow ftrace function tracepoint by users without CAP_SYS_ADMIN
            Disallow raw tracepoint access by users without CAP_SYS_ADMIN
        >=1: Disallow CPU event access by users without CAP_SYS_ADMIN
        >=2: Disallow kernel profiling by users without CAP_SYS_ADMIN
        """
        with open('/proc/sys/kernel/perf_event_paranoid', 'r') as f:
            val= int(f.read())
            if val != -1:
                raise Exception("Paranoid enable")

    def encode_events(self):
        """
            Find the configuration perf_event_attr for each event name
        """
        for group in self.event_groups_names:
            ev_list= []
            for e in group:
                #TODO check err
                err, encoding = perfmon.pfm_get_perf_event_encoding(e, perfmon.PFM_PLM0 | perfmon.PFM_PLM3, None, None)
                ev_list.append(encoding)
            self.event_groups.append(ev_list)

    def create_events(self):
        """
            Create the events from the perf_event_attr groups
        """
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
        """
            Close all file descriptors destroying the events
        """
        for group in self.fd_groups:
            for fd in group:
                os.close(fd)
        self.fd_groups= []

    def kill_program(self):
        """
            Kill the workload if still alive
        """
        if self.program and self.program.isAlive:
            print("Killing process", self.program.pid)
            self.program.start()
            os.kill(self.program.pid, signal.SIGKILL)

    def enable_events(self):
        """
            Enable the events
        """
        for fd in self.fd_groups:
            fcntl.ioctl(fd[0], profiler.PERF_EVENT_IOC_ENABLE, 0)

    def disable_events(self):
        """
            Disable the events
        """
        for fd in self.fd_groups:
            fcntl.ioctl(fd[0], profiler.PERF_EVENT_IOC_DISABLE, 0)

    def reset_events(self):
        for fd in self.fd_groups:
            fcntl.ioctl(fd[0], profiler.PERF_EVENT_IOC_RESET, 0)

    def read_events(self):
        """
            Read from the events
        """
        data= []
        for group in self.fd_groups:
            raw= os.read(group[0], 4096)
            to_read= int(len(raw)/8)
            raw= struct.unpack('q'*to_read ,raw)
            data+=raw
        return data

    def initialize(self):
        """
            Prepare to run the workload
        """
        try:
            self.destroy_events()
            self.kill_program()
            self.program= workload.Workload(workload.stringVec(self.program_args))
            self.program.MAX_SIZE_GROUP= 512
            self.create_events()
            for group in self.fd_groups:
                self.program.add_events(workload.intVec([group[0]]))
        except:
            self.kill_program()
            raise

    def run_python(self, period, reset=False):
        """
            period : float period of sampling in seconds
            reset : reset the counters on sampling

            Run the workload on background and sample on python
        """
        self.initialize()
        self.program.start()
        data= []
        while self.program.isAlive:
            time.sleep(period)
            data.append(self.read_events())
            if reset: self.reset_events()
        data.append(self.read_events())

        return self.format_data(data)
        
    def run(self, period, reset=False):
        """
        period : float period of sampling in seconds
        reset : reset the counters on sampling

        Run the workload and sample on the c++ module blocking
        """
        self.initialize()
        data= self.program.run(reset, period*1e6)
        aux= []
        for v in data:
            aux.append(list(v))
        
        return self.format_data(data)
    
    def format_data(self, data):
        """
        Format the data

        Event groups reading format
            id
            time
            counter 1
            ...
            counter n
        Event single format
            counter
        
        output:
            [
                [counter 1 ... counter n]
                ...
                [counter 1 ... counter n]
            ]
        """
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