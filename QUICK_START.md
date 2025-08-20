# 🚀 UsenetSync Quick Start Guide

## Project Structure
```
/workspace/
├── backend/        # Python API Server
│   └── src/       # Source code (add to PYTHONPATH)
├── frontend/       # React + Tauri Desktop App
│   └── src/       # React source code
└── docs/          # Documentation
```

## Environment Setup

### 1. Python Backend
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Set Python path
export PYTHONPATH=/workspace/backend/src
```

### 2. Frontend
```bash
cd frontend
npm install
```

## Running the Application

### Option 1: Using Make (Recommended)
```bash
make backend   # Start backend API
make frontend  # Start frontend UI
make dev       # Start both (requires tmux)
```

### Option 2: Manual
```bash
# Backend
python start_backend.py

# Frontend (new terminal)
cd frontend && npm run dev
```

## Testing
```bash
# All tests
make test

# Backend only
cd backend && PYTHONPATH=src pytest tests/

# Frontend only
cd frontend && npm test
```

## Common Issues

### Import Errors
- Ensure `PYTHONPATH=/workspace/backend/src`
- Python modules use dot notation: `unified.core.database`

### Port Conflicts
- Backend runs on port 8000
- Frontend runs on port 1420
- PostgreSQL on port 5432

### Database
- Default: SQLite at `data/usenetsync.db`
- Production: PostgreSQL (see `.env.example`)

## Development Tips

1. **Backend changes**: Restart with `make backend`
2. **Frontend changes**: Auto-reloads with Vite
3. **Add dependencies**: 
   - Backend: Add to `backend/requirements.txt`
   - Frontend: `cd frontend && npm install package-name`

## File Locations

- **Backend API**: `backend/src/unified/api/server.py`
- **Frontend App**: `frontend/src/App.tsx`
- **Database Schema**: `backend/src/unified/core/schema.py`
- **Configuration**: `.env` (copy from `.env.example`)

---
For detailed documentation, see [docs/README.md](docs/README.md)
