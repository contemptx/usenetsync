# UsenetSync - Clean Architecture

A unified Usenet synchronization and sharing system with a clean, organized codebase.

## 📁 Project Structure

```
/workspace/
├── backend/          # Python API Server
│   ├── src/         # Source code
│   │   └── unified/ # Main system modules
│   ├── tests/       # Backend tests
│   └── requirements.txt
│
├── frontend/         # Desktop Application
│   ├── src/         # React/TypeScript code
│   ├── src-tauri/   # Rust/Tauri wrapper
│   ├── tests/       # Frontend tests
│   └── package.json
│
├── data/            # Application data & databases
├── config/          # Configuration files
├── docs/            # Documentation
├── venv/            # Python virtual environment
└── obsolete/        # Old code (to be removed)
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Rust (for Tauri)
- PostgreSQL (optional)

### Installation
```bash
# Install all dependencies
make install

# Or manually:
pip install -r backend/requirements.txt
cd frontend && npm install
```

### Running the Application

#### Backend Server
```bash
make backend
# Or: python start_backend.py
```

#### Frontend Application
```bash
make frontend
# Or: cd frontend && npm run dev
```

#### Both (using tmux)
```bash
make dev
```

## 🧪 Testing

```bash
# Run all tests
make test

# Backend tests only
cd backend && pytest tests/

# Frontend tests only
cd frontend && npm test
```

## 📚 Documentation

- [Backend Documentation](backend/README.md)
- [Frontend Documentation](frontend/README.md)
- [API Documentation](docs/API.md)
- [Testing Guide](docs/TESTING_GUIDE.md)

## 🏗️ Architecture

### Backend (Python)
- **FastAPI** for REST API
- **PostgreSQL/SQLite** for database
- **Unified System** architecture for all operations
- **pynntp** for Usenet connectivity

### Frontend (React + Tauri)
- **React** with TypeScript
- **Tauri** for desktop integration
- **Vite** for fast development
- **Playwright** for E2E testing

## 🔧 Development

### Available Commands
```bash
make help       # Show all commands
make install    # Install dependencies
make backend    # Start backend
make frontend   # Start frontend
make test       # Run tests
make clean      # Clean artifacts
```

### Environment Variables
Create a `.env` file in the root:
```env
# Backend
DATABASE_URL=postgresql://user:pass@localhost/db
API_HOST=0.0.0.0
API_PORT=8000

# Frontend
VITE_BACKEND_URL=http://localhost:8000

# Usenet
NNTP_HOST=news.newshosting.com
NNTP_PORT=563
NNTP_USERNAME=your_username
NNTP_PASSWORD=your_password
```

## 📦 Building for Production

### Backend
```bash
cd backend
pip install pyinstaller
pyinstaller --onefile src/unified/main.py
```

### Frontend
```bash
cd frontend
npm run build
npm run tauri build
```

## 🤝 Contributing

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License - see [LICENSE](docs/LICENSE)

## 🧹 Recent Cleanup

- Reorganized structure for clarity
- Moved 200+ obsolete files to `/obsolete`
- Reduced repository size by 4.2GB
- Clear separation of backend and frontend
- Consistent naming conventions

---

**Status**: ✅ Clean, Organized, and Ready for Development
