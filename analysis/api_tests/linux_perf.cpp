#include <iostream>
#include <map>

#include <cstdio>
#include <cstdlib>
#include <math.h>
#include <string.h>
#include <errno.h>
#include <stdint.h>

#include <sys/wait.h>
#include <sys/syscall.h>
#include <sys/ptrace.h>
#include <sys/ioctl.h>
#include <linux/perf_event.h>
#include <linux/hw_breakpoint.h>
#include <asm/unistd.h>
#include <unistd.h>
#include <inttypes.h>
#include <sys/stat.h>
#include <fcntl.h>

#include <x86intrin.h>

using namespace std;

// struct read_format
// {
//     uint64_t nr;
//     struct
//     {
//         uint64_t value;
//         uint64_t id;
//     } values[];
// };
struct read_format
{
    uint64_t nr;           /* The number of events */
    uint64_t time_enabled; /* if PERF_FORMAT_TOTAL_TIME_ENABLED */
    uint64_t time_running; /* if PERF_FORMAT_TOTAL_TIME_RUNNING */
    struct
    {
        uint64_t value; /* The value of the event */
        uint64_t id;    /* if PERF_FORMAT_ID */
    } values[];
};

void flush_cache()
{
    const int chache_size= 10240;
    int cs= chache_size*1024/sizeof(double), i;
    double *flush= (double *)calloc(cs, sizeof(double)), tmp = 0.0;
    // #pragma omp parallel for reduction(+:tmp) private(i)
    for (i = 0; i < cs; i++)
        tmp += flush[i];
    free(flush);
}

int main(int argc, char **argv)
{
    pid_t pid = fork();
    if (pid == 0)
    {
        int fd= open("output",  O_WRONLY | O_CREAT, S_IRUSR | S_IWUSR);
        dup2(fd, STDOUT_FILENO);
        // flush_cache();
        ptrace(PTRACE_TRACEME, 0, 0, 0);
        int ret = execl(argv[1], (const char *)argv + 1, NULL);
        if (ret < 0)
        {
            cerr << "ERROR ON EXECL" << endl;
        }
    }
    else if (pid > 0)
    {
        int pmcs[11] = {PERF_COUNT_HW_INSTRUCTIONS,
                        PERF_COUNT_HW_BRANCH_INSTRUCTIONS,
                        PERF_COUNT_HW_BRANCH_MISSES,
                        PERF_COUNT_HW_CPU_CYCLES,
                        PERF_COUNT_HW_CACHE_REFERENCES,
                        PERF_COUNT_HW_CACHE_MISSES,
                        PERF_COUNT_HW_BUS_CYCLES,
                        PERF_COUNT_HW_STALLED_CYCLES_FRONTEND,
                        PERF_COUNT_HW_STALLED_CYCLES_BACKEND,
                        PERF_COUNT_HW_REF_CPU_CYCLES};

        map<int, int> aux;
        map<int, string> aux_str;
        aux_str[PERF_COUNT_HW_INSTRUCTIONS] = "PERF_COUNT_HW_INSTRUCTIONS";
        aux_str[PERF_COUNT_HW_CPU_CYCLES] = "PERF_COUNT_HW_CPU_CYCLES";
        aux_str[PERF_COUNT_HW_CACHE_REFERENCES] = "PERF_COUNT_HW_CACHE_REFERENCES";
        aux_str[PERF_COUNT_HW_CACHE_MISSES] = "PERF_COUNT_HW_CACHE_MISSES";
        aux_str[PERF_COUNT_HW_BRANCH_INSTRUCTIONS] = "PERF_COUNT_HW_BRANCH_INSTRUCTIONS";
        aux_str[PERF_COUNT_HW_BRANCH_MISSES] = "PERF_COUNT_HW_BRANCH_MISSES";
        aux_str[PERF_COUNT_HW_BUS_CYCLES] = "PERF_COUNT_HW_BUS_CYCLES";
        aux_str[PERF_COUNT_HW_STALLED_CYCLES_FRONTEND] = "PERF_COUNT_HW_STALLED_CYCLES_FRONTEND";
        aux_str[PERF_COUNT_HW_STALLED_CYCLES_BACKEND] = "PERF_COUNT_HW_STALLED_CYCLES_BACKEND";
        aux_str[PERF_COUNT_HW_REF_CPU_CYCLES] = "PERF_COUNT_HW_REF_CPU_CYCLES";
        aux_str[PERF_COUNT_HW_CACHE_LL] = "PERF_COUNT_HW_CACHE_LL";

        struct perf_event_attr pea;
        int fds[11];
        uint64_t ids[11];
        uint64_t vals[11];
        char buf[4096];
        struct read_format *rf = (struct read_format *)buf;
        int i;

        memset(&pea, 0, sizeof(struct perf_event_attr));
        pea.type = PERF_TYPE_HARDWARE;
        pea.size = sizeof(struct perf_event_attr);
        pea.config = pmcs[0];
        pea.disabled = 1;
        pea.pinned= 1;
        pea.exclude_kernel = 1;
        pea.exclude_hv = 1;
        // pea.sample_type= PERF_SAMPLE_CPU;
        // pea.sample_freq= 99;
        pea.read_format = PERF_FORMAT_GROUP | PERF_FORMAT_ID | PERF_FORMAT_TOTAL_TIME_ENABLED | PERF_FORMAT_TOTAL_TIME_RUNNING;
        fds[0] = syscall(__NR_perf_event_open, &pea, pid, -1, -1, 0);
        ioctl(fds[0], PERF_EVENT_IOC_ID, &ids[0]);
        aux[ids[0]] = pmcs[0];

        for (int i = 1; i < 4; i++)
        {
            memset(&pea, 0, sizeof(struct perf_event_attr));
            pea.type = PERF_TYPE_HARDWARE;
            pea.size = sizeof(struct perf_event_attr);
            pea.config = pmcs[i];
            pea.disabled = 1;
            pea.exclude_kernel = 1;
            pea.exclude_hv = 1;
            // pea.sample_type= PERF_SAMPLE_PERIOD;
            // pea.sample_freq= 99;
            pea.read_format = PERF_FORMAT_GROUP | PERF_FORMAT_ID | PERF_FORMAT_TOTAL_TIME_ENABLED | PERF_FORMAT_TOTAL_TIME_RUNNING;
            fds[i] = syscall(__NR_perf_event_open, &pea, pid, -1, fds[0] /*!!!*/, 0);
            ioctl(fds[i], PERF_EVENT_IOC_ID, &ids[i]);
            aux[ids[i]] = pmcs[i];
        }

        pea.type = PERF_TYPE_HW_CACHE;
        pea.config = PERF_COUNT_HW_CACHE_LL | (PERF_COUNT_HW_CACHE_OP_READ << 8) | (PERF_COUNT_HW_CACHE_RESULT_ACCESS << 16);
        pea.disabled = 1;
        pea.exclude_kernel = 1;
        pea.exclude_hv = 1;
        pea.read_format = PERF_FORMAT_GROUP | PERF_FORMAT_ID | PERF_FORMAT_TOTAL_TIME_ENABLED | PERF_FORMAT_TOTAL_TIME_RUNNING;

        fds[4] = syscall(__NR_perf_event_open, &pea, pid, -1, fds[0] /*!!!*/, 0);
        ioctl(fds[4], PERF_EVENT_IOC_ID, &ids[4]);
        aux[ids[4]] = PERF_COUNT_HW_CACHE_LL;

        ioctl(fds[0], PERF_EVENT_IOC_RESET, PERF_IOC_FLAG_GROUP);
        ioctl(fds[0], PERF_EVENT_IOC_ENABLE, PERF_IOC_FLAG_GROUP);
        int status;
        waitpid(pid, &status, 0);
        ptrace(PTRACE_CONT, pid, 0, 0);
        int acc= 0;
        while(1)
        {
            waitpid(pid, &status, 0);
            if (WIFEXITED(status))
                break;
        }
        ioctl(fds[0], PERF_EVENT_IOC_DISABLE, PERF_IOC_FLAG_GROUP);
        read(fds[0], buf, sizeof(buf));
        for (i = 0; i < rf->nr; i++)
        {
            vals[i] = rf->values[i].value;
            cout << aux_str[aux[rf->values[i].id]] << " : " << rf->values[i].value << endl;
        }
    }
}