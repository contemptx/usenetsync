"""
UsenetSync Test Configuration
Enforces real component usage with live Newshosting server
"""
import os
import sys
import socket
import importlib
import tempfile
from pathlib import Path
from typing import Any, Generator
import pytest

# Block nntplib to enforce pynntp usage
class BlockNntplib:
    def find_spec(self, fullname, path, target=None):
        if fullname == "nntplib":
            raise ImportError("nntplib is forbidden. UsenetSync uses pynntp (import as nntp)")
        return None

sys.meta_path.insert(0, BlockNntplib())

# Required environment variables for UsenetSync
REQUIRED_ENV = {
    "NNTP_HOST": "news.newshosting.com",
    "NNTP_PORT": "563",
    "NNTP_USERNAME": "contemptx",
    "NNTP_SSL": "true",
    "NNTP_GROUP": "alt.binaries.test",
    "DATABASE_URL": None,  # Value varies
    "USENET_CLIENT_MODULE": "unified.networking.real_nntp_client:RealNNTPClient",
    "INDEXING_MODULE": "unified.indexing.scanner:UnifiedScanner",
    "SEGMENTATION_MODULE": "unified.segmentation.processor:UnifiedSegmentProcessor",
}

def pytest_sessionstart(session):
    """Validate UsenetSync environment before tests"""
    
    # Check required variables
    missing = []
    wrong = []
    
    for var, expected in REQUIRED_ENV.items():
        actual = os.environ.get(var)
        if not actual:
            missing.append(var)
        elif expected and actual != expected:
            wrong.append(f"{var}={actual} (expected {expected})")
    
    if missing:
        raise RuntimeError(f"Missing UsenetSync env vars: {', '.join(missing)}")
    if wrong:
        raise RuntimeError(f"Wrong UsenetSync config: {', '.join(wrong)}")
    
    # Verify Newshosting is reachable
    try:
        socket.gethostbyname("news.newshosting.com")
    except Exception as e:
        raise RuntimeError(f"Cannot resolve news.newshosting.com: {e}")
    
    # Verify SSL port 563
    if os.environ["NNTP_PORT"] != "563":
        raise RuntimeError("UsenetSync requires port 563 (SSL)")
    
    print("\n✅ UsenetSync Test Environment Validated")
    print(f"   Server: {os.environ['NNTP_HOST']}:{os.environ['NNTP_PORT']}")
    print(f"   User: {os.environ['NNTP_USERNAME']}")
    print(f"   Database: {os.environ.get('DATABASE_URL', 'Not set')}")

@pytest.fixture
def real_nntp_client():
    """Get real UsenetSync NNTP client"""
    spec = os.environ["USENET_CLIENT_MODULE"]
    module_name, class_name = spec.split(":")
    module = importlib.import_module(module_name)
    return getattr(module, class_name)

@pytest.fixture
def real_indexing_scanner():
    """Get real UsenetSync indexing scanner"""
    spec = os.environ["INDEXING_MODULE"]
    module_name, class_name = spec.split(":")
    module = importlib.import_module(module_name)
    return getattr(module, class_name)

@pytest.fixture
def real_segmentation_processor():
    """Get real UsenetSync segmentation processor"""
    spec = os.environ["SEGMENTATION_MODULE"]
    module_name, class_name = spec.split(":")
    module = importlib.import_module(module_name)
    return getattr(module, class_name)

@pytest.fixture
def unified_system():
    """Get complete UnifiedSystem instance"""
    from unified.main import UnifiedSystem
    return UnifiedSystem()

@pytest.fixture
def test_files_dir() -> Generator[Path, None, None]:
    """Create temporary directory with real test files"""
    with tempfile.TemporaryDirectory(prefix="usenetsync_test_") as tmpdir:
        test_dir = Path(tmpdir)
        
        # Create various test files
        files = {
            "document.txt": b"This is a test document for UsenetSync.\n" * 100,
            "data.csv": b"id,name,value\n1,test,100\n2,demo,200\n" * 50,
            "binary.dat": bytes(range(256)) * 100,
            "large.bin": b"X" * (1024 * 1024),  # 1MB file
        }
        
        for name, content in files.items():
            (test_dir / name).write_bytes(content)
        
        # Create subdirectory with more files
        subdir = test_dir / "subdir"
        subdir.mkdir()
        for i in range(5):
            (subdir / f"file_{i}.txt").write_text(f"Subdir file {i}\n" * 20)
        
        yield test_dir

@pytest.fixture
def newshosting_connection():
    """Provide Newshosting connection details"""
    return {
        "host": os.environ["NNTP_HOST"],
        "port": int(os.environ["NNTP_PORT"]),
        "username": os.environ["NNTP_USERNAME"],
        "password": os.environ["NNTP_PASSWORD"],
        "ssl": os.environ["NNTP_SSL"].lower() == "true",
        "group": os.environ["NNTP_GROUP"],
    }