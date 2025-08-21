# 🚀 Trigger GUI Tests Now!

## Quick Link:
**➡️ https://github.com/contemptx/usenetsync/actions/workflows/gui-tests.yml**

## Steps:
1. Click the link above
2. Click **"Run workflow"** button (green button on right)
3. **⚠️ IMPORTANT**: Make sure "Enable debug mode" is **UNCHECKED** ❌
4. Branch: `master` ✅
5. Click green **"Run workflow"** button

## What Will Happen:
- Tests will run on 4 environments (Ubuntu/Windows × Node 18/20)
- If tests fail, AI triage will analyze (no debug hanging!)
- Autofix will create PR if needed
- 15-minute timeout on debug (if accidentally enabled)

## Why Tests Likely Failed:
Common reasons for GUI test failures:
- Missing dependencies (tauri-driver not installed)
- Frontend build issues
- Missing test files or configuration
- Environment setup problems

The AI triage system will identify and fix these automatically!

---
**Status**: Ready to run with fixes applied ✅