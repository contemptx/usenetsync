#!/bin/bash
# UsenetSync Test Runner
# Loads environment and runs tests with real components

# Colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check for .env file
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found${NC}"
    echo "Copy .env.example to .env and configure credentials"
    exit 1
fi

# Load environment variables
set -a
source .env
set +a

# Verify critical variables
if [ "$NNTP_HOST" != "news.newshosting.com" ]; then
    echo -e "${YELLOW}Warning: Not using news.newshosting.com${NC}"
fi

if [ "$NNTP_PORT" != "563" ]; then
    echo -e "${YELLOW}Warning: Not using port 563 (SSL)${NC}"
fi

# Set Python path
export PYTHONPATH=/workspace/src:$PYTHONPATH

# Activate virtual environment if not already active
if [ -z "$VIRTUAL_ENV" ]; then
    source /workspace/venv/bin/activate
fi

echo -e "${GREEN}UsenetSync Test Runner${NC}"
echo "Server: $NNTP_HOST:$NNTP_PORT"
echo "User: $NNTP_USERNAME"
echo "Database: PostgreSQL"
echo ""

# Run tests
cd /workspace/backend-python
pytest "$@"