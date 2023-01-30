#!/bin/bash

sudo apt update
sudo apt install g++ gcc swig libpfm4-dev python3-dev python3-pip
cd performance_features/
python3 setup.py build
python3 setup.py install
