# 📦 INSTALL ALL REQUIREMENTS FOR WINDOWS

## **Critical Modules You MUST Install:**

```powershell
# 1. PostgreSQL support (you already have this ✅)
pip install psycopg2-binary

# 2. USENET/NNTP support (CRITICAL - you probably don't have this!)
pip install pynntp

# 3. Encryption support
pip install cryptography PyNaCl

# 4. API Backend
pip install fastapi uvicorn[standard]

# 5. Redis (for caching)
pip install redis

# 6. Other important modules
pip install python-dotenv websockets aiofiles
```

## **Quick Install All At Once:**

```powershell
# Run this command to install everything:
pip install psycopg2-binary pynntp cryptography PyNaCl fastapi uvicorn[standard] redis python-dotenv websockets aiofiles prometheus-client psutil click rich pyyaml watchdog zstandard
```

## **Verify Installation:**

After installing, verify the critical ones work:

```powershell
# Test imports
python -c "import psycopg2; print('✅ PostgreSQL ready')"
python -c "import nntp; print('✅ Usenet/NNTP ready')"
python -c "import cryptography; print('✅ Encryption ready')"
python -c "import nacl; print('✅ Ed25519 keys ready')"
python -c "import fastapi; print('✅ API backend ready')"
```

## **Why Each Module is Required:**

| Module | Purpose | Critical? |
|--------|---------|-----------|
| **pynntp** | Connects to Usenet servers for upload/download | ✅ YES |
| **psycopg2-binary** | PostgreSQL database for production | ✅ YES |
| **cryptography** | AES-256 encryption for files | ✅ YES |
| **PyNaCl** | Ed25519 keys for user authentication | ✅ YES |
| **fastapi** | Backend API server | ✅ YES |
| **redis** | Caching for performance | ⚠️ Important |
| **websockets** | Real-time updates to GUI | ⚠️ Important |

## **Common Issues:**

### If `pynntp` fails to install:
```powershell
# Try installing with --no-deps first
pip install --no-deps pynntp

# Then install its dependencies
pip install nntp
```

### If you get "Microsoft Visual C++ 14.0 is required":
- Install Visual Studio Build Tools from: https://visualstudio.microsoft.com/downloads/
- Or use pre-compiled wheels:
```powershell
pip install --only-binary :all: cryptography
```

## **After Installation:**

Once all modules are installed, the app will:
1. ✅ Connect to PostgreSQL for data storage
2. ✅ Connect to Usenet servers for file operations
3. ✅ Encrypt/decrypt files with AES-256
4. ✅ Generate user keys with Ed25519
5. ✅ Run the full API backend

Then you can run:
```powershell
cd C:\git\usenetsync\usenet-sync-app
npm run tauri dev
```

And everything will work with FULL functionality!