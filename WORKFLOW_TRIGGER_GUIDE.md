# GitHub Actions Workflow Trigger Guide

## Current Status
- **Branch**: `cursor/unify-indexing-and-download-systems-e32c`
- **Latest Commit**: `ci: trigger workflow run`
- **Workflow File**: `.github/workflows/gui-tests.yml`

## Step 1: Check Billing Status

### Go to GitHub Billing Settings
1. Navigate to: https://github.com/settings/billing
2. Check "Actions" section for:
   - Current usage
   - Remaining minutes
   - Billing status

### If Billing Issue Exists:
- **Option A**: Update payment method
- **Option B**: Switch to GitHub Free (2000 minutes/month)
- **Option C**: Use self-hosted runners (free unlimited)

## Step 2: Check Workflow Status

### Direct Links:
1. **Actions Page**: https://github.com/contemptx/usenetsync/actions
2. **Workflows List**: https://github.com/contemptx/usenetsync/actions/workflows
3. **GUI Tests Workflow** (if available): Look for "GUI Tests" in the list

## Step 3: Trigger the Workflow

### Method 1: Manual Trigger (Recommended)
1. Go to: https://github.com/contemptx/usenetsync/actions
2. Click on "GUI Tests" workflow (left sidebar)
3. Click "Run workflow" button (right side)
4. Select:
   - Branch: `cursor/unify-indexing-and-download-systems-e32c`
   - Debug mode: `false` (or `true` for detailed logs)
5. Click green "Run workflow" button

### Method 2: Create a Pull Request
```bash
# Create PR to trigger workflow
git checkout cursor/unify-indexing-and-download-systems-e32c
git checkout -b trigger/gui-tests
git push origin trigger/gui-tests
```
Then create PR on GitHub to `main` or `develop`

### Method 3: Push Another Commit
```bash
# Make a small change to trigger
echo "# Trigger $(date)" >> README.md
git add README.md
git commit -m "ci: trigger workflow"
git push origin cursor/unify-indexing-and-download-systems-e32c
```

## Step 4: Monitor the Workflow

Once triggered, you'll see:

### Workflow Overview
```
GUI Tests #1
├── Ubuntu (Node 18.x) 🔄 Running...
├── Ubuntu (Node 20.x) 🔄 Running...
├── Windows (Node 18.x) 🔄 Running...
└── Windows (Node 20.x) 🔄 Running...
```

### Expected Timeline
- **0:00** - Workflow starts
- **0:30** - Setup begins
- **2:00** - Dependencies installed
- **4:00** - Tauri app built
- **6:00** - Tests running
- **10:00** - Tests complete
- **11:00** - AI triage (if failures)
- **12:00** - Autofix PR created (if applicable)

## Step 5: View Results

### Success Scenario ✅
- Green checkmark on all jobs
- Test artifacts available for download
- Allure report generated

### Failure Scenario ❌
1. **AI Triage runs automatically**
   - Downloads test artifacts
   - Analyzes failures
   - Creates GitHub issue

2. **Autofix attempts**
   - Applies suggested fixes
   - Creates pull request
   - Re-runs tests

## What Each Job Does

### Test Execution (4 parallel jobs)
```yaml
OS: [Ubuntu, Windows]
Node: [18.x, 20.x]
```

Each job:
1. Installs dependencies
2. Builds Tauri app
3. Runs GUI tests
4. Takes screenshots
5. Generates reports

### AI Triage (on failure)
```python
# Analyzes:
- JUnit XML results
- Screenshot differences  
- Error patterns
- Suggests fixes
```

### Autofix (if possible)
```javascript
// Automatically:
- Updates selectors
- Fixes timeouts
- Adjusts config
- Creates PR
```

## Troubleshooting

### Workflow Not Appearing
**Possible causes:**
1. Billing issue not resolved
2. Workflow file has syntax error
3. Branch protection rules

**Solution:**
- Check billing status
- Validate YAML syntax
- Check branch permissions

### Workflow Fails Immediately
**Possible causes:**
1. Missing secrets/variables
2. Invalid workflow syntax
3. Permission issues

**Solution:**
- Check repository settings → Secrets
- Validate workflow file
- Check Actions permissions

### Tests Fail
**Expected on first run:**
1. tauri-driver not installed → CI installs it
2. No baseline screenshots → First run creates them
3. Path issues → AI will suggest fixes

## Manual Test Run (Alternative)

If GitHub Actions still has issues, run locally:

```bash
# Install Rust (if not installed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

# Install tauri-driver
cargo install tauri-driver

# Run tests
cd frontend
npm install
npm run build
npm run build:tauri
npm run test:e2e
```

## Expected Outcomes

### First Run
- Some failures expected
- Baseline screenshots created
- AI analyzes issues
- Fixes suggested/applied

### Subsequent Runs
- Tests should pass
- Visual regression detected
- Performance metrics tracked
- Reports generated

## Contact for Help

If issues persist:
1. Check Actions tab for detailed logs
2. Review AI-generated issue (if created)
3. Check autofix PR (if created)
4. The system is self-healing and will improve with each run!

## Quick Commands

```bash
# Check latest commit
git log --oneline -1

# View workflow file
cat .github/workflows/gui-tests.yml

# Check if on correct branch
git branch --show-current

# Push trigger commit
git commit --allow-empty -m "ci: trigger workflow"
git push
```

---

**Remember**: The AI system will help diagnose and fix most issues automatically!