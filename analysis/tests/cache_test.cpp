#include <iostream>
#include <x86intrin.h>

using namespace std;

void flush_cache()
{
    const int chache_size= 10240;
    int cs= chache_size*1024/sizeof(double), i;
    double *flush= (double *)calloc(cs, sizeof(double)), tmp = 0.0;
    #pragma omp parallel for reduction(+:tmp) private(i)
    for (i = 0; i < cs; i++)
        tmp += flush[i];
    free(flush);
}

uint32_t* acess_me;

void sink(uint32_t x) {
  (void)x;
}

uint64_t time_mem_acss()
{
    uint64_t a, b;
    a = __rdtsc();
    sink(acess_me[0]);
    _mm_lfence();
    b = __rdtsc();
    return b-a;
}

int main()
{
    acess_me= new uint32_t;
    *acess_me= 0xabcd;
    double cmax= 100, mean= 0;
    for(int i=0; i<cmax; i++)
    {
        flush_cache();
        cout << time_mem_acss() << " ";
        sink(acess_me[0]);
        cout << time_mem_acss() << endl;
    }
    // for(int i=0; i<cmax; i++)
    // {
    //     flush_cache();
    //     //_mm_clflush((void*)(acess_me)); //flush the specifc adress
    //     mean+=time_mem_acss();
    // }
    // cout << mean/cmax << endl;
    // sink(acess_me[0]);
    // mean=0;
    // for(int i=0; i<cmax; i++)
    // {
    //     mean+=time_mem_acss();
    // }
    // cout << mean/cmax << endl;
}