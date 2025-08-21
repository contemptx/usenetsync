# 🛑 Cancel Stuck Workflow & Re-run

## Step 1: Cancel the Stuck Workflow
**Direct link to cancel:** https://github.com/contemptx/usenetsync/actions/runs/17123220214

1. Click the link above
2. Click the **Cancel workflow** button (⬜ icon) in the top right
3. Confirm cancellation

## Step 2: Monitor New Runs
The fix has already triggered new workflow runs that won't get stuck:

| Workflow | Status | Notes |
|----------|--------|-------|
| GUI Tests | Will run after push | Has 15-min timeout on debug |
| live-fullstack | 🔄 Running | Testing backend |
| Simple Windows Build | 🔄 Running | Building installer |

## Step 3: Trigger Clean GUI Test Run (Optional)
If GUI Tests don't auto-start after canceling:

1. Go to: https://github.com/contemptx/usenetsync/actions/workflows/gui-tests.yml
2. Click **"Run workflow"** button
3. **IMPORTANT**: Leave "Enable debug mode" **unchecked**
4. Select branch: `master`
5. Click green **"Run workflow"**

## ✅ What's Fixed:
- Debug sessions now timeout after 15 minutes
- Debug mode properly checks for 'true' string
- Won't hang indefinitely anymore

## 📊 Expected Behavior:
- Tests run normally
- If tests fail → AI triage analyzes
- If fixable → Autofix creates PR
- No more hanging on SSH debug!

---

The tmate debug feature is useful for interactive debugging but should only be enabled when specifically needed. The timeout ensures it won't block CI/CD indefinitely.