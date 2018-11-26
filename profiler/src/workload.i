%module workload
%{
    #include "workload.h"
%}

%include "std_string.i"
%include "std_vector.i"
%include "std_pair.i"
%include "std_map.i"
%include "stdint.i"

%catches(const char*) Workload::Workload();

%include "workload.h"

namespace std
{
    %template(stringVec) vector<string>;
    %template(intVec) vector<int>;
    %template(int64Vec) vector<signed long int>;
    %template(int64VecVec) vector<vector<signed long int>>;
}
