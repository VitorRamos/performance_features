#!/bin/bash

sudo apt update
sudo apt install g++7 gcc-7 swig libpfm4-dev python3-dev
cd profiler/
python setup.py install