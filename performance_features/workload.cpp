
#include "workload.h"

#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/ptrace.h>
#include <sys/wait.h>
#include <memory.h>

#include <linux/perf_event.h>

#include <iostream>
#include <sys/mman.h>
#include <sys/sysinfo.h>
#include <sys/fcntl.h>
#include <sys/ioctl.h>

using namespace std;

char** convert(const vector<string>& v)
{
    char** args= new char*[v.size()+1];
    for(unsigned int i=0; i<v.size(); i++)
        args[i]= const_cast<char*>(v[i].c_str());
    args[v.size()]= nullptr;
    return args;
}

Workload::Workload(vector<string> args)
{
    this->pid= create_wrokload(args);
    this->isAlive= 1;
    ppid= getpid();

    struct sigaction sa;
    sigemptyset(&sa.sa_mask);
    sa.sa_sigaction = Workload::handler;
    sa.sa_flags = SA_SIGINFO; /* Important. */
    sigaction(SIGUSR1, &sa, NULL);
}

int Workload::create_wrokload(const vector<string>& args)
{
    int pid = fork();
    if(pid < 0)
        throw "Error on fork";
    if (pid == 0)
    {
        char **argv= convert(args);
        int fd = open("out.stdout", O_WRONLY | O_CREAT, S_IRUSR | S_IWUSR);
        //int oldfd= dup(STDOUT_FILENO);
        dup2(fd, STDOUT_FILENO);
        fd = open("out.stderr", O_WRONLY | O_CREAT, S_IRUSR | S_IWUSR);
        dup2(fd, STDERR_FILENO);
        if(ptrace(PTRACE_TRACEME, 0, 0, 0) < 0)
        {
            std::cerr << "Cant traceme" << std::endl;
            exit(-1);
        }
        if (execv(argv[0], argv) < 0)
        {
            std::cerr << "Cant creat process" << std::endl;
            //dup2(oldfd, STDOUT_FILENO);
            //ptrace(PTRACE_DETACH, 0, 0, 0);
            //throw "Error on fork";
            //this->isAlive= 0; // need to comunitate
            exit(-1);
        }
    }
    else
    {
        return pid;
    }
    return 0;
}

void Workload::wait_finish()
{
    int status;
    while(waitpid(pid, &status, 0) >= 0)
    {
        if (WIFEXITED(status) || WIFSIGNALED(status))
            break;

        if(WIFSTOPPED(status) && WSTOPSIG(status) == SIGTRAP)
        {
            union sigval sv;
            sv.sival_int = pid;
            sigqueue(ppid, SIGUSR1, sv);
        }
    }
    isAlive= 0;
}

void Workload::start()
{
    if(isAlive)
    {
        int status;
        waitpid(pid, &status, 0);
        if(ptrace(PTRACE_CONT, pid, 0, 0) < 0)
            throw "Cant continue program";
        // waitpid(pid, &status, 0);
        // cout << "Ptrace 2 " << ptrace(PTRACE_CONT, pid, 0, 0) << endl;
        // waitpid(pid, &status, 0);
        // cout << "Ptrace 3 " << ptrace(PTRACE_CONT, pid, 0, 0) << endl;
        waiter = new thread(&Workload::wait_finish, this);
    }
}

void Workload::add_events(std::vector<int> fds_)
{
    fds.insert(fds.end(), fds_.begin(), fds_.end());
}

vector<vector<signed long int>> Workload::run(double sample_perid, bool reset)
{
    vector<vector<signed long int>> samples;
    vector<signed long int> row(MAX_SIZE_GROUP);
    ssize_t bytes_read;
    unsigned int i;
    int status;
    int hangs= sample_perid>=0?WNOHANG:0;
    samples.reserve(1000);

    if(!this->isAlive)
        throw "Attempt to execute a dead program";

    waitpid(pid, &status, 0);
    for(i=0; i<fds.size(); i++)
    {
        ioctl(fds[i], PERF_EVENT_IOC_RESET, PERF_IOC_FLAG_GROUP);
        ioctl(fds[i], PERF_EVENT_IOC_ENABLE, PERF_IOC_FLAG_GROUP);
    }
    if(ptrace(PTRACE_CONT, pid, 0, 0) < 0)
        throw "Cant continue program";
    while(1)
    {
        waitpid(pid, &status, hangs);
        if (WIFEXITED(status) || WIFSIGNALED(status))
            break;
        if(WIFSTOPPED(status))
        {
            if(WSTOPSIG(status) == SIGABRT)
                break;
            if(WSTOPSIG(status) == SIGCHLD)
                ptrace(PTRACE_CONT, pid, 0, 0);
            // continue;
        }

        if(sample_perid) usleep(sample_perid);

        bytes_read= 0;
        for(i=0; i<fds.size(); i++)
        {
            bytes_read+= read(fds[i], &row[bytes_read/sizeof(signed long int)], MAX_SIZE_GROUP*sizeof(signed long int));
            if(reset) ioctl(fds[i], PERF_EVENT_IOC_RESET, PERF_IOC_FLAG_GROUP);
            // if(bytes_read <= 0)
            //     throw "Error on sampling ";
        }
        row.resize(bytes_read/sizeof(signed long int));
        samples.push_back(row);
    }
    isAlive= 0;
    bytes_read= 0;
    for(i=0; i<fds.size(); i++)
    {
        bytes_read+= read(fds[i], &row[bytes_read/sizeof(signed long int)], MAX_SIZE_GROUP*sizeof(signed long int));
        if(reset) ioctl(fds[i], PERF_EVENT_IOC_RESET, PERF_IOC_FLAG_GROUP);
        // if(bytes_read <= 0)
        //     throw "Error on sampling ";
    }
    row.resize(bytes_read/sizeof(signed long int));
    samples.push_back(row);
    return samples;
}
