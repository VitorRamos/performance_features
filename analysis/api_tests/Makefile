all: papi event

papi: papi.cpp
	g++ papi.cpp -lpapi -o papi_perf

event: linux_perf.cpp
	g++ linux_perf.cpp -o linux_perf

clean:
	rm papi_perf linux_perf