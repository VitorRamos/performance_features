#!/bin/bash

sudo apt update
sudo apt install g++ gcc swig libpfm4-dev python3-dev
cd profiler/
pip install -r requirements.txt
python setup.py build
python setup.py install