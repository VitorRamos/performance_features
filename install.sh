#!/bin/bash

sudo apt update
sudo apt install g++ gcc swig libpfm4-dev python3-dev
cd profiler/
python setup.py install