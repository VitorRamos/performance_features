CC=g++

all: cache_test sample_teste

cache_test: cache_test.o
cache_test.o: cache_test.cpp

sample_teste: sample_teste.o
	$(CC) $< -lpfm -o $@
sample_teste.o: sample_teste.cpp

clean:
	rm *.o
	rm cache_test sample_teste
