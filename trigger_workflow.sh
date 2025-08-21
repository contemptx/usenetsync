#!/bin/bash

echo "=========================================="
echo "Triggering GitHub Actions Workflow"
echo "=========================================="

# Try to trigger via a small commit
echo ""
echo "Option 1: Creating a small commit to trigger workflow..."
cd /workspace

# Add a timestamp to a test file to trigger the workflow
echo "# Workflow trigger: $(date)" >> .github/workflows/gui-tests.yml
git add .github/workflows/gui-tests.yml
git commit -m "ci: trigger workflow run $(date +%s)"
git push origin cursor/unify-indexing-and-download-systems-e32c

echo ""
echo "✅ Pushed commit to trigger workflow"
echo ""
echo "=========================================="
echo "Check the workflow status at:"
echo "https://github.com/contemptx/usenetsync/actions"
echo "=========================================="
echo ""
echo "If billing is resolved, the workflow should start within 1-2 minutes"
echo ""
echo "Alternative options if workflow doesn't start:"
echo "1. Go to https://github.com/contemptx/usenetsync/actions"
echo "2. Find 'GUI Tests' workflow"
echo "3. Click 'Run workflow' button"
echo "4. Select the branch: cursor/unify-indexing-and-download-systems-e32c"
echo "5. Click 'Run workflow'"