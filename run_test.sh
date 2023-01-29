#!/bin/bash

./kernel_parameters.sh
cd tests/
python run.py -v
