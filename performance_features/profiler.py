"""
    This module provie a high level api to linux perf events witout overhead while executing

    How it works:
        Using perfmon python wrapper to the system calls and structures the file descriptors are created
        The file descriptors are passed to the workload module develop on c++ wich start the target application and sample the file descriptors

"""

from . import workload
import perfmon
import time, struct, os, signal, fcntl


class Profiler:
    PERF_EVENT_IOC_ENABLE = 0x2400
    PERF_EVENT_IOC_DISABLE = 0x2401
    PERF_EVENT_IOC_ID = 0x80082407
    PERF_EVENT_IOC_RESET = 0x2403

    def __init__(self, events_groups, program_args=None):
        """
        program_args : list with program name and arguments to run
        events_groups : list of list of event names, each list is a event group with event leader the first name
        """
        self.event_groups_names = events_groups
        self.event_groups = []
        self.fd_groups = []
        self.program_args = program_args
        self.program = None
        self.__check_paranoid()
        self.__encode_events()

    def __del__(self):
        self.__destroy_events()

    def __check_paranoid(self):
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
        with open("/proc/sys/kernel/perf_event_paranoid", "r") as f:
            val = int(f.read())
            if val >= 2:
                raise Exception("Paranoid enable")

    def __encode_events(self):
        """
        Find the configuration perf_event_attr for each event name
        """
        for group in self.event_groups_names:
            ev_list = []
            for e in group:
                # TODO check err
                if "SYSTEMWIDE" in e:
                    e = e.split(":")[1]
                try:
                    err, encoding = perfmon.pfm_get_perf_event_encoding(
                        e, perfmon.PFM_PLM0 | perfmon.PFM_PLM3, None, None
                    )
                except:
                    # print("Error encoding : "+e)
                    raise
                ev_list.append(encoding)
            self.event_groups.append(ev_list)

    def __create_events(self, pid):
        """
        Create the events from the perf_event_attr groups
        """
        for group, group_name in zip(self.event_groups, self.event_groups_names):
            fd_list = []
            if len(group) > 1:
                e = group[0]
                e.exclude_kernel = 1
                e.exclude_hv = 1
                e.inherit = 1
                e.disabled = 1
                e.read_format = (
                    perfmon.PERF_FORMAT_GROUP | perfmon.PERF_FORMAT_TOTAL_TIME_ENABLED
                )
                fd = perfmon.perf_event_open(e, pid, -1, -1, 0)
                if fd < 1:
                    raise Exception("Error creating fd " + group_name[0])
                fd_list.append(fd)
                for e, e_name in zip(group[1:], group_name[1:]):
                    e.exclude_kernel = 1
                    e.exclude_hv = 1
                    e.inherit = 1
                    e.disabled = 1
                    e.read_format = (
                        perfmon.PERF_FORMAT_GROUP
                        | perfmon.PERF_FORMAT_TOTAL_TIME_ENABLED
                    )
                    fd = perfmon.perf_event_open(e, pid, -1, fd_list[0], 0)
                    if fd < 1:
                        raise Exception("Error creating fd " + e_name)
                    fd_list.append(fd)
            else:
                for e, e_name in zip(group, group_name):
                    if "SYSTEMWIDE" in e_name:
                        fd = perfmon.perf_event_open(e, -1, 0, -1, 0)
                    else:
                        e.exclude_kernel = 1
                        e.exclude_hv = 1
                        e.inherit = 1
                        e.disabled = 1
                        fd = perfmon.perf_event_open(e, pid, -1, -1, 0)

                    if fd < 0:
                        raise Exception("Erro creating fd " + e_name)
                    fd_list.append(fd)
            self.fd_groups.append(fd_list)

    def __destroy_events(self):
        """
        Close all file descriptors destroying the events
        """
        for group in self.fd_groups:
            for fd in group:
                os.close(fd)
        self.fd_groups = []

    def __kill_program(self):
        """
        Kill the workload if still alive
        """
        if self.program and self.program.isAlive:
            print("Killing process", self.program.pid)
            self.program.start()
            os.kill(self.program.pid, signal.SIGKILL)
            t_max = 0
            while self.program.isAlive and t_max < 50:
                time.sleep(0.1)
                t_max += 1
            if t_max >= 50:
                raise Exception("Cant kill the program")

    def __initialize(self):
        """
        Prepare to run the workload
        """
        # TODO solve the race condition
        try:
            self.__destroy_events()
            # self.__kill_program()
            self.program = workload.Workload(workload.stringVec(self.program_args))
            self.program.MAX_SIZE_GROUP = 512
            self.__create_events(self.program.pid)
            for group in self.fd_groups:
                self.program.add_events(workload.intVec([group[0]]))
        except Exception as e:
            # self.__kill_program()
            # if "Error on fork" in str(e):
            #     print(os.getpid())
            #     exit(0)
            # print("After")
            raise
        finally:
            pass  # something really bad happen

    def __format_data(self, data):
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
        all_data = []
        for s in data:
            only_s = []
            s = list(s)
            c = 0
            for g in self.event_groups_names:
                if len(g) > 1:
                    only_s += s[c + 2 : c + 2 + len(g)]
                    c = c + 2 + len(g)
                else:
                    only_s += [s[c]]
                    c += 1
            all_data.append(only_s)
        return all_data

    def set_program(self, program_args):
        """
        Set the program args
        """
        self.program_args = program_args

    def enable_events(self):
        """
        Enable the events
        """
        for fd in self.fd_groups:
            for fdx in fd:
                fcntl.ioctl(fdx, Profiler.PERF_EVENT_IOC_ENABLE, 0)

    def disable_events(self):
        """
        Disable the events
        """
        for fd in self.fd_groups:
            for fdx in fd:
                fcntl.ioctl(fdx, Profiler.PERF_EVENT_IOC_DISABLE, 0)

    def reset_events(self):
        """
        Reset the events
        """
        for fd in self.fd_groups:
            for fdx in fd:
                fcntl.ioctl(fdx, Profiler.PERF_EVENT_IOC_RESET, 0)

    def read_events(self):
        """
        Read from the events
        """
        data = []
        for group in self.fd_groups:
            raw = os.read(group[0], 4096)
            to_read = int(len(raw) / 8)
            raw = struct.unpack("q" * to_read, raw)
            data += raw
        return data

    def start_counters(self, pid):
        """
        Reset and start the counters
        """
        self.__create_events(pid)
        self.reset_events()
        self.enable_events()

    def run_python(self, sample_period, reset_on_sample=False):
        """
        sample_period : float period of sampling in seconds
        reset_on_sample : reset the counters on sampling

        return: samples

        Run the workload on background and sample on python
        """
        if not self.program_args:
            raise Exception("Need a program ars tor run")

        if sample_period < 0:
            self.__initialize()
            self.reset_events()
            self.enable_events()
            self.program.start()
            data = []
            while self.program.isAlive:
                time.sleep(0.05)
                data.append(self.read_events())

            return self.__format_data(data)

        self.__initialize()
        self.reset_events()
        self.enable_events()
        self.program.start()
        data = []
        while self.program.isAlive:
            time.sleep(sample_period)
            data.append(self.read_events())
            if reset_on_sample:
                self.reset_events()

        data.append(self.read_events())

        return self.__format_data(data)

    def run_background(self):
        """
        Run the program on backgroun, not sampling
        """
        if not self.program_args:
            raise Exception("Need a program ars tor run")
        self.__initialize()
        self.reset_events()
        self.enable_events()
        self.program.start()

    def run(self, sample_period, reset_on_sample=False):
        """
        sample_period : float period of sampling in seconds
        reset_on_sample : reset the counters on sampling

        return: samples

        Run the workload and sample on the c++ module blocking
        """
        if not self.program_args:
            raise Exception("Need a program ars tor run")
        self.__initialize()
        data = self.program.run(sample_perid=sample_period * 1e6, reset=reset_on_sample)
        aux = [list(v) for v in data]
        return self.__format_data(aux)


def run_program(pargs, to_monitor, n=30, sample_period=0.05, reset_on_sample=False):
    """
    Run the program multiple times
    """
    try:
        all_data = []
        for i in range(n):
            program = Profiler(program_args=pargs, events_groups=to_monitor)
            data = program.run(
                sample_period=sample_period, reset_on_sample=reset_on_sample
            )
            all_data.append(data)
    except RuntimeError as e:
        print(e.args[0])
    data = {
        "n": n,
        "sample_period": sample_period,
        "reset_on_sample": reset_on_sample,
        "data": all_data,
        "to_monitor": to_monitor,
    }

    return data


def save_data(data, name):
    """
    save data to file
    """
    import pickle

    with open("{}.dat".format(name), "wb+") as f:
        pickle.dump(data, f)
