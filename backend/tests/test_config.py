"""
Test configuration for UsenetSync
Uses environment variables for all sensitive data
"""
import os
from dotenv import load_dotenv

# Load test-specific environment file
load_dotenv('.env.test')

# NNTP Configuration
NNTP_HOST = os.getenv('NNTP_HOST', 'news.newshosting.com')
NNTP_PORT = int(os.getenv('NNTP_PORT', '563'))
NNTP_USERNAME = os.getenv('NNTP_USERNAME')
NNTP_PASSWORD = os.getenv('NNTP_PASSWORD')
NNTP_SSL = os.getenv('NNTP_SSL', 'true').lower() == 'true'
NNTP_GROUP = os.getenv('NNTP_GROUP', 'alt.binaries.test')

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://usenetsync:usenetsync123@localhost:5432/usenetsync')
DATABASE_TYPE = os.getenv('DATABASE_TYPE', 'postgresql')

# Validation
if not all([NNTP_USERNAME, NNTP_PASSWORD]):
    raise ValueError(
        "NNTP credentials not set. Please set NNTP_USERNAME and NNTP_PASSWORD "
        "in your environment or .env.test file"
    )

# Test helpers
def get_test_nntp_client():
    """Get a configured NNTP client for testing"""
    from unified.networking.real_nntp_client import RealNNTPClient
    
    client = RealNNTPClient()
    client.connect(NNTP_HOST, NNTP_PORT, NNTP_SSL)
    client.authenticate(NNTP_USERNAME, NNTP_PASSWORD)
    return client

def get_test_database():
    """Get a configured database for testing"""
    from unified.core.database import UnifiedDatabase, DatabaseConfig, DatabaseType
    
    db_type = DatabaseType.POSTGRESQL if DATABASE_TYPE == 'postgresql' else DatabaseType.SQLITE
    config = DatabaseConfig(db_type=db_type)
    
    if db_type == DatabaseType.POSTGRESQL:
        # Parse DATABASE_URL
        import re
        match = re.match(r'postgresql://([^:]+):([^@]+)@([^:/]+):(\d+)/(.+)', DATABASE_URL)
        if match:
            user, password, host, port, database = match.groups()
            config.pg_user = user
            config.pg_password = password
            config.pg_host = host
            config.pg_port = int(port)
            config.pg_database = database
    
    return UnifiedDatabase(config)