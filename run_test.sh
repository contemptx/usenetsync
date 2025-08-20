#!/bin/bash
cd /workspace
/usr/bin/python3 run_real_test_now.py > real_output.txt 2>&1
echo "Exit code: $?" >> real_output.txt