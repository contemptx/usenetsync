#!/bin/bash
# Run the production client test
cd /workspace
/usr/bin/python3 use_production_client.py 2>&1
echo "Exit code: $?"
echo "Test complete - checking for output files..."
ls -la /workspace/PRODUCTION_TEST*