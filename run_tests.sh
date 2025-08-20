#!/bin/bash
# Load environment variables from .env file and run tests

set -a  # Export all variables
source .env
set +a

# Run the tests with PYTHONPATH set
cd backend-python
PYTHONPATH=/workspace/src pytest "$@"