#include <papi.h>
#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <unistd.h>
#include <math.h>
#include <sys/ptrace.h>
#include <sys/wait.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>

using namespace std;

void handle_error(int x)
{
    cout << "ERROR " << x << endl;
    exit(x);
}

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

int main(int argc, char** argv)
{
    pid_t pid= fork();
    if(pid == 0)
    {
        int fd= open("output",  O_WRONLY | O_CREAT, S_IRUSR | S_IWUSR);
        dup2(fd, STDOUT_FILENO);
        ptrace(PTRACE_TRACEME, 0, 0, 0);
        // flush_cache();
        int ret= execl(argv[1], (const char*)argv+1, NULL);
        if(ret < 0)
        {
            cerr << "ERROR ON EXECL" << endl;
        }
    }
    else if(pid > 0)
    {
        int EventSet = PAPI_NULL;
        int retval;

        /* Initialize the PAPI library */
        retval = PAPI_library_init(PAPI_VER_CURRENT);

        if (retval != PAPI_VER_CURRENT)
        {
            fprintf(stderr, "PAPI library init error!\n");
            exit(1);
        }

        /* Create an EventSet */
        if (PAPI_create_eventset(&EventSet) != PAPI_OK)
            handle_error(1);

        /* Add Total Instructions Executed to our EventSet */
        if (PAPI_add_event(EventSet, PAPI_TOT_INS) != PAPI_OK)
            handle_error(1);
        
        /* Add Total Instructions Executed to our EventSet */
        if (PAPI_add_event(EventSet, PAPI_BR_INS) != PAPI_OK)
            handle_error(1);
        
        if (PAPI_add_event(EventSet, PAPI_BR_MSP) != PAPI_OK)
            handle_error(1);
        
        if (PAPI_add_event(EventSet, PAPI_L3_TCR) != PAPI_OK)
            handle_error(1);

        if(PAPI_attach(EventSet, pid) != PAPI_OK)
            handle_error(1);

        int status;
        waitpid(pid, &status, 0);
        PAPI_start(EventSet);            
        ptrace(PTRACE_CONT, pid, 0, 0);
        long long arr[8];
        while(1)
        {
            waitpid(pid, &status, 0);
            if (WIFEXITED(status))
                break;
        }
        PAPI_stop(EventSet, arr);
        PAPI_read(EventSet, arr);
        cout << "TOTAL INSTRUCTIONS : " << arr[0] << endl;
        cout << "BRANCH INSTRUCTIONS : " << arr[1] << endl;
        cout << "BRANCH MISPREDICT : " << arr[2] << endl;
        cout << "TOTAL CACHE READ L3 : " << arr[3] << endl;
    }
}