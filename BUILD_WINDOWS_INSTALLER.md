# 🔨 Building Windows Installer for UsenetSync

## Important Note
**Windows installers (`.exe`, `.msi`) must be built on a Windows machine.** The current repository is set up on Linux, so the installer files don't exist yet but all the configuration is ready.

## Where Installers Will Be Located After Building

Once built on Windows, the installers will be located at:
- **NSIS Installer**: `usenet-sync-app/src-tauri/target/release/bundle/nsis/UsenetSync_1.0.0_x64-setup.exe`
- **MSI Installer**: `usenet-sync-app/src-tauri/target/release/bundle/msi/UsenetSync_1.0.0_x64_en-US.msi`

## How to Build the Windows Installer

### Option 1: Build on Windows Machine (Required)

1. **Clone the repository on Windows**:
```powershell
git clone https://github.com/contemptx/usenetsync.git
cd usenetsync
```

2. **Install Prerequisites**:
   - **Node.js 18+**: https://nodejs.org/
   - **Rust**: https://rustup.rs/
   - **Visual Studio Build Tools 2022**: https://visualstudio.microsoft.com/downloads/
     - Select "Desktop development with C++" workload
   - **NSIS** (for .exe installer): https://nsis.sourceforge.io/Download
   - **WiX Toolset v3** (for .msi installer): https://wixtoolset.org/releases/

3. **Install Dependencies**:
```powershell
cd usenet-sync-app
npm install
```

4. **Build the Application and Installers**:
```powershell
# Build everything (app + installers)
npm run tauri build

# Or build specific installer types:
npm run tauri build -- --bundles nsis    # For .exe installer only
npm run tauri build -- --bundles msi     # For .msi installer only
npm run tauri build -- --bundles nsis,msi # For both
```

5. **Find Your Installers**:
After successful build, installers will be in:
```
usenet-sync-app/
└── src-tauri/
    └── target/
        └── release/
            └── bundle/
                ├── nsis/
                │   └── UsenetSync_1.0.0_x64-setup.exe  ← NSIS Installer
                └── msi/
                    └── UsenetSync_1.0.0_x64_en-US.msi  ← MSI Installer
```

### Option 2: GitHub Actions (Automated CI/CD)

Create `.github/workflows/build-windows.yml`:

```yaml
name: Build Windows Installer

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:

jobs:
  build-windows:
    runs-on: windows-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: 18
          
      - name: Install Rust
        uses: dtolnay/rust-toolchain@stable
        
      - name: Install dependencies
        run: |
          cd usenet-sync-app
          npm install
          
      - name: Build Tauri App
        run: |
          cd usenet-sync-app
          npm run tauri build
          
      - name: Upload NSIS Installer
        uses: actions/upload-artifact@v3
        with:
          name: UsenetSync-Setup
          path: usenet-sync-app/src-tauri/target/release/bundle/nsis/*.exe
          
      - name: Upload MSI Installer
        uses: actions/upload-artifact@v3
        with:
          name: UsenetSync-MSI
          path: usenet-sync-app/src-tauri/target/release/bundle/msi/*.msi
          
      - name: Create Release
        if: startsWith(github.ref, 'refs/tags/')
        uses: softprops/action-gh-release@v1
        with:
          files: |
            usenet-sync-app/src-tauri/target/release/bundle/nsis/*.exe
            usenet-sync-app/src-tauri/target/release/bundle/msi/*.msi
          draft: false
          prerelease: false
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

Then push a tag to trigger the build:
```bash
git tag v1.0.0
git push origin v1.0.0
```

### Option 3: Cross-Compilation (Experimental)

While Tauri doesn't officially support cross-compilation for Windows bundles from Linux, you can try:

1. **Install Windows target for Rust**:
```bash
rustup target add x86_64-pc-windows-msvc
```

2. **Install Wine and NSIS**:
```bash
sudo apt-get install wine wine64 nsis
```

3. **Attempt cross-build**:
```bash
cd usenet-sync-app
npm run tauri build -- --target x86_64-pc-windows-msvc
```

**Note**: This often fails due to Windows-specific dependencies and is not recommended for production builds.

## Current Repository Status

✅ **What's Ready**:
- All source code
- Tauri configuration (`tauri.conf.json`)
- NSIS installer script (`src-tauri/windows/installer.nsi`)
- Icons and assets
- Build configuration

❌ **What's Not Built Yet**:
- `UsenetSync-1.0.0-Setup.exe` (NSIS installer)
- `UsenetSync_1.0.0_x64_en-US.msi` (MSI installer)
- `UsenetSync.exe` (Windows executable)

These files will only exist after building on a Windows machine.

## Quick Windows Build Commands

Once on a Windows machine with all prerequisites installed:

```powershell
# Quick build (from repository root)
cd usenet-sync-app
npm install
npm run tauri build

# The installer will be created at:
# src-tauri\target\release\bundle\nsis\UsenetSync_1.0.0_x64-setup.exe
```

## Troubleshooting

### "NSIS not found"
- Download and install NSIS: https://nsis.sourceforge.io/Download
- Add NSIS to PATH: `C:\Program Files (x86)\NSIS`

### "WiX not found" 
- Download WiX Toolset v3: https://wixtoolset.org/releases/
- Restart after installation

### "cargo not found"
- Install Rust: https://rustup.rs/
- Restart terminal after installation

### Build fails with "cannot find -lwebview2"
- This is a Windows-specific library
- Must build on Windows, not Linux/WSL

## Summary

The installer files (`UsenetSync-1.0.0-Setup.exe` and `.msi`) don't exist in the repository because:
1. They are build artifacts, not source code
2. They must be built on Windows
3. They are typically not committed to git (too large)

To get the installer, you need to:
1. **Clone this repo on a Windows machine**
2. **Install the prerequisites**
3. **Run `npm run tauri build`**
4. **Find the installer in `src-tauri/target/release/bundle/`**

Or wait for automated builds via GitHub Actions if configured.