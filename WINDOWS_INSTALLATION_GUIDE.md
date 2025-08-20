# 🪟 Windows Installation Guide for UsenetSync

## 📊 **SYSTEM STATUS**

### **Backend Status: ⚠️ PARTIALLY INTEGRATED**
- ✅ **Unified Python Backend Created** - All modules consolidated in `/src/unified/`
- ✅ **API Server Ready** - FastAPI server with all endpoints
- ✅ **GUI Bridge Created** - `gui_backend_bridge.py` connects to Tauri
- ⚠️ **NOT YET CONNECTED** - Tauri still calls old fragmented code in `/src/cli.py`
- ❌ **Real Usenet Testing** - Not fully tested with real server

### **Frontend Status: ✅ COMPLETE**
- ✅ **React Frontend** - Full UI with all screens
- ✅ **Tauri Framework** - Rust backend for native integration
- ✅ **46 Tauri Commands** - All commands implemented
- ✅ **Dependencies** - All npm packages configured
- ⚠️ **Integration Needed** - Must update to call unified backend

### **GUI Components:**
```
✅ Login/Registration Screen
✅ Dashboard with Statistics
✅ Folder Management
✅ Upload Queue
✅ Download Manager
✅ Share Management
✅ Settings Panel
✅ Real-time Progress Updates
✅ Dark/Light Theme
```

---

## 🚀 **WINDOWS INSTALLATION INSTRUCTIONS**

### **Prerequisites**

1. **Install Python 3.11+** (NOT 3.12 or 3.13 - compatibility issues)
   - Download from: https://www.python.org/downloads/
   - ✅ Check "Add Python to PATH" during installation

2. **Install Node.js 20+**
   - Download from: https://nodejs.org/
   - Includes npm

3. **Install Visual Studio Build Tools**
   - Download from: https://visualstudio.microsoft.com/downloads/
   - Select "Desktop development with C++"
   - Required for Rust/Tauri compilation

4. **Install Rust**
   - Download from: https://www.rust-lang.org/tools/install
   - Run: `rustup-init.exe`

5. **Install Git**
   - Download from: https://git-scm.com/download/win

---

## 📦 **INSTALLATION STEPS**

### **Step 1: Clone Repository**
```powershell
git clone https://github.com/yourusername/usenetsync.git
cd usenetsync
```

### **Step 2: Install Python Dependencies**
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install pynntp  # CRITICAL - for Usenet connection
pip install -r requirements.txt
```

### **Step 3: Install Frontend Dependencies**
```powershell
cd usenet-sync-app
npm install
```

### **Step 4: Configure Usenet Credentials**
Create `usenet_sync_config.json` in the root directory:
```json
{
  "servers": [
    {
      "name": "newshosting_primary",
      "hostname": "news.newshosting.com",
      "port": 563,
      "username": "YOUR_USERNAME",
      "password": "YOUR_PASSWORD",
      "use_ssl": true,
      "max_connections": 10,
      "priority": 1,
      "enabled": true
    }
  ],
  "database": {
    "type": "sqlite",
    "path": "usenetsync.db"
  },
  "security": {
    "message_id_domain": "ngPost.com",
    "subject_length": 20,
    "use_obfuscation": true
  }
}
```

### **Step 5: Initialize Database**
```powershell
# From root directory
python setup_database.py
```

### **Step 6: Start the Application**

#### **Option A: Development Mode**
```powershell
# Terminal 1: Start Python backend
python src/gui_backend_bridge.py --mode api --port 8000

# Terminal 2: Start Tauri/React frontend
cd usenet-sync-app
npm run tauri dev
```

#### **Option B: Build for Production**
```powershell
cd usenet-sync-app
npm run tauri build

# Installer will be in:
# usenet-sync-app\src-tauri\target\release\bundle\msi\
```

---

## 🔧 **CRITICAL CONFIGURATION**

### **1. Update Tauri to Use Unified Backend**

Edit `usenet-sync-app/src-tauri/src/main.rs`:
```rust
// Change from old CLI
let output = Command::new("python")
    .arg("src/cli.py")  // OLD
    
// To unified backend
let output = Command::new("python")
    .arg("src/gui_backend_bridge.py")  // NEW
```

### **2. Update React API Calls**

Edit `usenet-sync-app/src/lib/api.ts`:
```typescript
// Change from Tauri commands
await invoke('create_user', { username });  // OLD

// To unified API
await fetch('http://localhost:8000/api/v1/users', {  // NEW
  method: 'POST',
  body: JSON.stringify({ username })
});
```

### **3. Fix Python Path Issues**

If Python commands fail, create `run_backend.bat`:
```batch
@echo off
cd /d "%~dp0"
call venv\Scripts\activate
python src\gui_backend_bridge.py --mode api --port 8000
```

---

## 🐛 **TROUBLESHOOTING**

### **Issue: "No module named 'nntp'"**
```powershell
pip install pynntp
# Note: Imports as 'nntp', not 'pynntp'
```

### **Issue: "Tauri build fails"**
```powershell
# Install WebView2
# Download from: https://developer.microsoft.com/en-us/microsoft-edge/webview2/

# Clear Rust cache
cargo clean
npm run tauri build
```

### **Issue: "Python backend won't start"**
```powershell
# Check Python version (must be 3.11)
python --version

# Reinstall dependencies
pip uninstall -y -r requirements.txt
pip install -r requirements.txt
```

### **Issue: "Database locked"**
```powershell
# Stop all Python processes
taskkill /F /IM python.exe

# Delete lock file
del usenetsync.db-wal
del usenetsync.db-shm
```

---

## ⚠️ **IMPORTANT NOTES**

### **What Works:**
- ✅ GUI launches and displays
- ✅ All UI components render
- ✅ Theme switching
- ✅ Basic navigation

### **What Needs Connection:**
- ⚠️ Folder indexing (calls old `cli.py`)
- ⚠️ Upload/Download (calls old fragmented code)
- ⚠️ Share management (not connected to unified)
- ⚠️ Real Usenet operations (needs testing)

### **To Make It Fully Functional:**

1. **Update all Tauri commands** in `src-tauri/src/main.rs` to call `gui_backend_bridge.py`
2. **Test with real Usenet server** using your credentials
3. **Verify subject format** (20 random chars) and message ID format (`@ngPost.com`)
4. **Run end-to-end test** of complete flow

---

## 📱 **Quick Start for Testing**

```powershell
# 1. Quick setup
git clone [repo]
cd usenetsync
python -m venv venv
.\venv\Scripts\activate
pip install pynntp psycopg2-binary cryptography fastapi uvicorn
pip install -r requirements.txt

# 2. Configure
copy usenet_sync_config.template.json usenet_sync_config.json
# Edit with your credentials

# 3. Test backend
python src/unified/main.py test

# 4. Launch GUI
cd usenet-sync-app
npm install
npm run tauri dev
```

---

## 🚨 **CRITICAL PATH TO PRODUCTION**

1. **Connect GUI to Unified Backend** ⬅️ PRIORITY
2. **Test with Real Usenet Server**
3. **Verify Security (20-char subjects, ngPost.com IDs)**
4. **Build Windows Installer**
5. **Sign with Code Certificate**

The system architecture is complete but the connection between the new unified backend and the existing GUI needs to be established. The GUI currently bypasses the unified system and calls the old fragmented code directly.