# UsenetSync

<p align="center">
  <img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/encryption-AES--256-red.svg" alt="AES-256 Encryption">
  <img src="https://img.shields.io/github/last-commit/contemptx/usenetsync" alt="Last Commit">
</p>

Secure Usenet folder synchronization system with end-to-end encryption, designed for scalability and supporting millions of files.

## 🚀 Features

- **🔒 End-to-End Encryption**: Military-grade AES-256-GCM encryption with RSA-4096 key exchange
- **📁 Scalable Architecture**: Efficiently handles millions of files with optimized indexing
- **🌐 Usenet Integration**: Leverages Usenet's global infrastructure for reliable file distribution
- **👥 Multi-User Support**: Public, private, and password-protected shares
- **🔄 Smart Synchronization**: Incremental updates and version tracking
- **📊 Comprehensive Monitoring**: Real-time performance metrics and health checks
- **🛡️ Security First**: Zero-knowledge architecture with secure key management
- **🚦 Production Ready**: Battle-tested with extensive error handling and recovery

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage](#usage)
- [Architecture](#architecture)
- [Security](#security)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## 💻 Installation

### Prerequisites

- Python 3.8 or higher
- NNTP server access (Usenet provider)
- SQLite 3.x
- 1GB+ RAM recommended

### Install from Source

```bash
# Clone the repository
git clone https://github.com/contemptx/usenetsync.git
cd usenetsync

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install UsenetSync
python setup.py install
```

## 🎯 Quick Start

### 1. Initialize the System

```bash
python cli.py init
```

### 2. Configure NNTP Settings

Edit `usenet_sync_config.json`:

```json
{
  "nntp": {
    "server": "news.yourprovider.com",
    "port": 563,
    "username": "your_username",
    "password": "your_password",
    "use_ssl": true
  }
}
```

### 3. Index a Folder

```bash
python cli.py index /path/to/folder --name "My Documents"
```

### 4. Create a Share

```bash
# Public share
python cli.py publish folder_id --type public

# Private share with specific users
python cli.py publish folder_id --type private --users alice,bob

# Password-protected share
python cli.py publish folder_id --type password --password "secret123"
```

### 5. Download a Share

```bash
python cli.py download SHARE_ACCESS_STRING --output /path/to/destination
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file (see `.env.example`):

```env
NNTP_SERVER=news.provider.com
NNTP_PORT=563
NNTP_USER=username
NNTP_PASS=password
USENETSYNC_LOG_LEVEL=INFO
```

### Advanced Configuration

See [Configuration Guide](docs/configuration.md) for detailed options.

## 📖 Usage

### Command Line Interface

```bash
# Show help
python cli.py --help

# List indexed folders
python cli.py list-folders

# Show folder details
python cli.py info folder_id

# Monitor system status
python cli.py monitor

# Run in daemon mode
python cli.py daemon
```

### Python API

```python
from usenet_sync import UsenetSync

# Initialize
sync = UsenetSync(config_path="config.json")

# Index a folder
folder_id = sync.index_folder("/path/to/folder", "My Folder")

# Create a private share
share_info = sync.publish_folder(
    folder_id,
    share_type="private",
    allowed_users=["alice", "bob"]
)

# Download a share
sync.download_share(share_access_string, "/destination")
```

## 🏗️ Architecture

UsenetSync uses a modular architecture:

- **Core System**: Main synchronization engine
- **Security Layer**: Encryption and authentication
- **Database Layer**: SQLite with connection pooling
- **NNTP Client**: Optimized Usenet communication
- **Upload System**: Parallel segment uploading
- **Download System**: Concurrent retrieval and reconstruction
- **Monitoring**: Real-time metrics and alerting

See [Architecture Documentation](docs/ARCHITECTURE.md) for details.

## 🔒 Security

- **Encryption**: AES-256-GCM for files, RSA-4096 for keys
- **Zero-Knowledge**: Server never sees unencrypted data
- **Key Management**: Secure key derivation and storage
- **Authentication**: Multi-factor user verification
- **Audit Logging**: Complete activity tracking

See [Security Overview](SECURITY.md) for details.

## 🛠️ Development

### Setting Up Development Environment

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run with coverage
pytest --cov=usenet_sync

# Run security scan
python security_audit_system.py scan .

# Format code
black .

# Check style
flake8
```

### AI-Assisted Development

This project uses AI-assisted development. See [AI Integration Guide](docs/AI_INTEGRATION.md).

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Quick Contribution Guide

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'feat: add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Usenet community for the robust infrastructure
- Contributors and testers
- Open source cryptography libraries

## 📞 Support

- 📧 Email: contemptx@me.com
- 💬 Discussions: [GitHub Discussions](https://github.com/contemptx/usenetsync/discussions)
- 🐛 Issues: [GitHub Issues](https://github.com/contemptx/usenetsync/issues)

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/contemptx">contemptx</a>
</p>
