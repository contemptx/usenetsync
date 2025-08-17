#!/usr/bin/env python3
"""
Simple NNTP connection test
"""

import sys
import time
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_nntp_connection():
    """Test NNTP server connection"""
    print("=" * 60)
    print("NNTP CONNECTION TEST")
    print("=" * 60)
    print()
    
    try:
        # Import required modules
        from src.config.secure_config import SecureConfigLoader
        from src.networking.production_nntp_client import ProductionNNTPClient
        
        # Load configuration
        print("Loading configuration...")
        config_loader = SecureConfigLoader()
        config = config_loader.config
        server_config = config['servers'][0]
        
        print(f"Server: {server_config['hostname']}")
        print(f"Port: {server_config['port']}")
        print(f"SSL: {server_config['use_ssl']}")
        print(f"Username: {server_config['username'][:3]}...")
        print()
        
        # Create NNTP client
        print("Creating NNTP client...")
        nntp_client = ProductionNNTPClient(
            host=server_config['hostname'],
            port=server_config['port'],
            username=server_config['username'],
            password=server_config['password'],
            use_ssl=server_config['use_ssl'],
            max_connections=server_config.get('max_connections', 4)
        )
        
        # Test connection
        print("Testing connection...")
        try:
            # Use connection as context manager
            with nntp_client.connection_pool.get_connection() as conn:
                print("✅ Connection successful!")
                print(f"  Connected to {conn.host}:{conn.port}")
                
                # Get server info
                print("\nTesting basic operations:")
                try:
                    # Post a test message to alt.test
                    test_message = f"Test message from UsenetSync at {time.time()}"
                    headers = {
                        'From': 'test@usenetsync.local',
                        'Subject': 'Connection Test',
                        'Newsgroups': 'alt.test',
                        'Message-ID': f'<test-{int(time.time())}@usenetsync.local>'
                    }
                    body = test_message
                    
                    result = nntp_client.post_article(headers, body, 'alt.test')
                    if result and result[0] == 240:
                        print(f"  ✅ Test post successful: {result[1]}")
                    else:
                        print(f"  ⚠️ Test post result: {result}")
                except Exception as e:
                    print(f"  Could not post test: {e}")
                
                return True
                
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_nntp_connection()
    sys.exit(0 if success else 1)