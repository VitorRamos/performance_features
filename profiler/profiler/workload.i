%module workload
%{
    #include "workload.h"
%}

%include "std_string.i"
%include "std_vector.i"
%include "std_pair.i"
%include "std_map.i"
%include "stdint.i"

%catches(const char*) Workload::Workload(std::vector<std::string> args);
%catches(const char*) Workload::run(double, bool);
%catches(const char*) Workload::start();

%include "workload.h"

namespace std
{
    %template(stringVec) vector<string>;
    %template(intVec) vector<int>;
    %template(int64Vec) vector<signed long int>;
    %template(int64VecVec) vector<vector<signed long int>>;
}
