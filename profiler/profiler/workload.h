
#include <exception>
#include <thread>
#include <vector>
#include <string>

class Workload
{
    //int pipe_fd[2];
    std::vector<int> fds;
    std::vector<std::string> args;
    std::thread* waiter;
private:
    int create_wrokload(const std::vector<std::string>& args);
    void wait_finish();
public:
    int MAX_SIZE_GROUP= 512;
    int pid, isAlive;

    Workload(std::vector<std::string> args);

    // start at background
    void start();

    // stat forground and sample on fds
    void add_events(std::vector<int> fds_);
    std::vector<std::vector<signed long int>> run(double sample_perid, bool reset);
};