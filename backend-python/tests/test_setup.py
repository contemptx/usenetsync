"""Test that the setup is working correctly"""
import os
import sys

def test_pythonpath():
    """Test that PYTHONPATH includes src directory"""
    assert any('src' in path for path in sys.path), "src directory not in PYTHONPATH"

def test_env_variables_exist():
    """Test that required environment variables are set"""
    # These should exist even if some have placeholder values
    required = ["NNTP_HOST", "NNTP_PORT", "DATABASE_URL"]
    for var in required:
        assert os.getenv(var) is not None, f"Missing environment variable: {var}"

def test_imports():
    """Test that key modules can be imported"""
    try:
        from unified.networking.nntp_adapter import NNTPAdapter
        from unified.networking.real_nntp_client import RealNNTPClient
        assert True
    except ImportError as e:
        assert False, f"Failed to import: {e}"