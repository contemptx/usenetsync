# 🚀 GitHub Actions Setup for Automated Windows Builds

## ✅ Setup Complete!

The GitHub Actions workflow has been added to your repository. Now you can automatically build Windows installers!

## How to Trigger a Build

### Option 1: Manual Trigger (Immediate)
1. Go to: https://github.com/contemptx/usenetsync/actions
2. Click on "Build Windows Installer" workflow
3. Click "Run workflow" button
4. Select branch: `master`
5. Click "Run workflow"
6. Wait ~10-15 minutes for build to complete
7. Download installers from the workflow artifacts

### Option 2: Create a Release (Recommended)
```bash
# From your local repository (or use GitHub UI)
git tag v1.0.0
git push origin v1.0.0
```

This will:
- Trigger the build automatically
- Create installers
- Create a GitHub Release
- Attach installers to the release
- Make them publicly downloadable

## What Gets Built

The workflow creates:
1. **NSIS Installer**: `UsenetSync_1.0.0_x64-setup.exe` (~50-100 MB)
2. **MSI Installer**: `UsenetSync_1.0.0_x64_en-US.msi` (~50-100 MB)

## Download Locations

After the workflow completes:

### From Workflow Run (Manual Trigger):
1. Go to: https://github.com/contemptx/usenetsync/actions
2. Click on the completed workflow run
3. Scroll down to "Artifacts"
4. Download:
   - `UsenetSync-NSIS-Installer` (contains .exe)
   - `UsenetSync-MSI-Installer` (contains .msi)

### From Release Page (Tag Trigger):
1. Go to: https://github.com/contemptx/usenetsync/releases
2. Find the latest release
3. Download installers from "Assets" section

## Fix for Your Local Build

You got an error because you were in the wrong directory. Here's the correct way:

```powershell
# You were in: C:\git\usenetsync
# But package.json is in: C:\git\usenetsync\usenet-sync-app

# Correct commands:
cd C:\git\usenetsync\usenet-sync-app
npm install
npm run tauri build

# Installer will be created at:
# C:\git\usenetsync\usenet-sync-app\src-tauri\target\release\bundle\nsis\UsenetSync_1.0.0_x64-setup.exe
```

## Quick Start Commands

### For Windows (Local Build):
```powershell
# Navigate to correct directory
cd C:\git\usenetsync\usenet-sync-app

# Install dependencies
npm install

# Build application and create installer
npm run tauri build

# Find installer at:
# src-tauri\target\release\bundle\nsis\UsenetSync_1.0.0_x64-setup.exe
```

### For GitHub Actions (Automated):
```bash
# Option 1: Manual trigger
# Go to GitHub Actions page and click "Run workflow"

# Option 2: Create a release
git tag v1.0.0
git push origin v1.0.0
```

## Workflow Status

Check build status at:
https://github.com/contemptx/usenetsync/actions/workflows/build-windows.yml

## Troubleshooting

### If GitHub Actions fails:
1. Check the workflow logs for errors
2. Common issues:
   - Missing Rust toolchain → Fixed in workflow
   - Missing Node.js → Fixed in workflow  
   - Windows-specific dependencies → Handled by windows-latest runner

### If local build fails:
1. Make sure you're in `usenet-sync-app` directory
2. Install prerequisites:
   - Node.js 18+
   - Rust (via rustup)
   - Visual Studio Build Tools 2022
3. Clear cache and retry:
   ```powershell
   npm cache clean --force
   rm -r node_modules
   npm install
   ```

## Next Steps

1. **Trigger a build now**:
   - Go to: https://github.com/contemptx/usenetsync/actions
   - Click "Build Windows Installer"
   - Click "Run workflow"

2. **Wait for completion** (~10-15 minutes)

3. **Download installer** from artifacts

4. **Install and test** on Windows

The installer will include everything:
- UsenetSync application
- PostgreSQL (auto-installed if needed)
- Python runtime
- All dependencies
- Desktop shortcuts
- Start menu entries

## Summary

✅ GitHub Actions workflow is now configured
✅ You can build installers automatically
✅ No need for local Windows build environment
✅ Installers will be available as downloads

**Your Windows installer will be ready in ~15 minutes after triggering the workflow!**