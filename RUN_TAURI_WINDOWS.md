# 🚀 Running Tauri Dev on Windows

## Quick Start Command:
```bash
cd frontend
npm run tauri dev
```

## Step-by-Step Instructions:

### 1. First Time Setup (if not done already):
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Install Rust (if not installed)
# Download from: https://www.rust-lang.org/tools/install
```

### 2. Start the Backend (in a separate terminal):
```bash
# Terminal 1 - Start the Python backend
python start_backend_full.py
```

### 3. Run Tauri Dev Mode:
```bash
# Terminal 2 - Start Tauri development
cd frontend
npm run tauri dev
```

## Alternative Commands:

### If `npm run tauri dev` doesn't work:
```bash
# Direct Tauri command
cd frontend
npx tauri dev

# Or with Cargo
cd frontend/src-tauri
cargo tauri dev
```

### Just Frontend (without Tauri shell):
```bash
cd frontend
npm run dev
# Opens in browser at http://localhost:1420
```

## Common Issues & Fixes:

### Issue: "tauri is not recognized"
```bash
# Install Tauri CLI
npm install -D @tauri-apps/cli
```

### Issue: Backend connection refused
```bash
# Make sure backend is running on port 8000
python start_backend_full.py
```

### Issue: Missing dependencies
```bash
cd frontend
npm install
```

### Issue: Rust/Cargo not found
Download and install from: https://www.rust-lang.org/tools/install
- Run the installer
- Restart terminal after installation

## Environment Variables:
Make sure `.env` file exists in root with:
```
VITE_BACKEND_URL=http://localhost:8000
```

## What Happens:
1. Vite dev server starts (frontend)
2. Rust compiles the Tauri app
3. Native window opens with your app
4. Hot reload enabled for development
5. DevTools available (Right-click → Inspect)

## Ports Used:
- Frontend (Vite): http://localhost:1420
- Backend (FastAPI): http://localhost:8000
- Tauri IPC: Internal

---

**Quick Command Summary:**
```bash
# Two terminals needed:
# Terminal 1:
python start_backend_full.py

# Terminal 2:
cd frontend && npm run tauri dev
```