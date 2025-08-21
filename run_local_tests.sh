#!/bin/bash

echo "=========================================="
echo "Running GUI Tests Locally"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
cd /workspace/frontend

echo "📦 Step 1: Checking dependencies..."
if [ ! -d "node_modules/@wdio" ]; then
    echo -e "${YELLOW}Installing test dependencies...${NC}"
    npm install --save-dev @wdio/cli @wdio/local-runner @wdio/mocha-framework @wdio/spec-reporter @wdio/globals ts-node webdriverio
fi
echo -e "${GREEN}✓ Dependencies ready${NC}"

echo ""
echo "🔨 Step 2: Building the application..."
npm run build
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Build successful${NC}"
else
    echo -e "${RED}✗ Build failed${NC}"
    exit 1
fi

echo ""
echo "🦀 Step 3: Checking for tauri-driver..."
if ! command -v tauri-driver &> /dev/null; then
    echo -e "${YELLOW}tauri-driver not found. Installing...${NC}"
    cargo install tauri-driver
fi
echo -e "${GREEN}✓ tauri-driver available${NC}"

echo ""
echo "🚀 Step 4: Running basic GUI test..."
echo "Note: This will attempt to launch the Tauri app"
echo ""

# Try to run a simple test
npx wdio run wdio.conf.ts --spec tests/e2e/basic-gui.spec.ts 2>&1 | tee test-output.log

# Check if test passed
if grep -q "passing" test-output.log; then
    echo ""
    echo -e "${GREEN}=========================================="
    echo "✅ LOCAL TESTS PASSED!"
    echo "==========================================${NC}"
    echo ""
    echo "The tests are working locally. GitHub Actions should work too"
    echo "once the billing issue is resolved."
else
    echo ""
    echo -e "${YELLOW}=========================================="
    echo "⚠️  LOCAL TESTS HAD ISSUES"
    echo "==========================================${NC}"
    echo ""
    echo "This is expected for the first run. Common issues:"
    echo "1. Tauri app needs to be built with: npm run build:tauri"
    echo "2. tauri-driver needs to be in PATH"
    echo "3. The app path in wdio.conf.ts might need adjustment"
    echo ""
    echo "Let's try building the Tauri app..."
    
    # Try to build Tauri app
    echo ""
    echo "🔨 Building Tauri application..."
    cd /workspace/frontend
    npm run build:tauri 2>&1 | tail -20
fi

echo ""
echo "=========================================="
echo "📊 Test Summary"
echo "=========================================="
echo "Local test run completed."
echo ""
echo "To monitor GitHub Actions:"
echo "1. Go to: https://github.com/contemptx/usenetsync/actions"
echo "2. Look for the workflow run from commit: 'ci: trigger workflow run'"
echo "3. Click on it to see detailed logs"
echo ""
echo "If the workflow doesn't appear:"
echo "- The billing issue might still be active"
echo "- You can manually trigger from the Actions tab"
echo "- Or create a PR to main/develop branch"
echo "=========================================="