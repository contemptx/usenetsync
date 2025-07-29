#!/usr/bin/env python3
"""
Create configuration file for UsenetSync
"""

import json
import os
import getpass


def create_config():
    """Create config.json with user input"""
    
    print("UsenetSync Configuration Setup")
    print("=" * 50)
    print("\nThis will create a config.json file for NNTP access.")
    print("You'll need your Usenet provider credentials.\n")
    
    # Get server details
    print("Enter your NNTP server details:")
    server = input("Server hostname (e.g., news.newshosting.com): ").strip()
    
    # Get port
    port_str = input("Port number (default 563 for SSL): ").strip()
    port = int(port_str) if port_str else 563
    
    # SSL
    ssl_str = input("Use SSL? (Y/n): ").strip().lower()
    use_ssl = ssl_str != 'n'
    
    # Credentials
    print("\nEnter your credentials:")
    username = input("Username: ").strip()
    password = getpass.getpass("Password: ")
    
    # Number of connections
    conn_str = input("\nNumber of connections (default 10): ").strip()
    connections = int(conn_str) if conn_str else 10
    
    # Test newsgroup
    newsgroup = input("Test newsgroup (default alt.binaries.test): ").strip()
    if not newsgroup:
        newsgroup = "alt.binaries.test"
    
    # Create config
    config = {
        "nntp": {
            "server": server,
            "port": port,
            "ssl": use_ssl,
            "username": username,
            "password": password,
            "connections": connections
        },
        "newsgroup": newsgroup,
        "test_mode": True,
        "upload": {
            "max_segment_size": 768000,
            "segments_per_upload": 10,
            "newsgroup": newsgroup,
            "upload_workers": 3
        },
        "download": {
            "temp_dir": "temp",
            "max_concurrent_downloads": 5
        }
    }
    
    # Save config
    with open("config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print(f"\n✓ Created config.json")
    print(f"  Server: {server}:{port} (SSL: {use_ssl})")
    print(f"  Username: {username}")
    print(f"  Connections: {connections}")
    print(f"  Test newsgroup: {newsgroup}")
    
    return True


def create_test_config():
    """Create a test configuration (no real credentials)"""
    
    config = {
        "nntp": {
            "server": "news.example.com",
            "port": 563,
            "ssl": True,
            "username": "test_user",
            "password": "test_pass",
            "connections": 10
        },
        "newsgroup": "alt.binaries.test",
        "test_mode": True,
        "upload": {
            "max_segment_size": 768000,
            "segments_per_upload": 10,
            "newsgroup": "alt.binaries.test",
            "upload_workers": 3
        },
        "download": {
            "temp_dir": "temp",
            "max_concurrent_downloads": 5
        }
    }
    
    with open("config.test.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print("✓ Created config.test.json (for testing without real server)")
    print("  This config won't connect to a real server")
    print("  Use it to test other components")
    
    return True


def main():
    """Main configuration setup"""
    
    if os.path.exists("config.json"):
        print("config.json already exists!")
        overwrite = input("Overwrite? (y/N): ").strip().lower()
        if overwrite != 'y':
            print("Keeping existing config.json")
            return
    
    print("\nChoose configuration type:")
    print("1. Real NNTP server configuration")
    print("2. Test configuration (no real server)")
    
    choice = input("\nEnter choice (1-2): ").strip()
    
    if choice == "1":
        create_config()
        print("\n✓ Configuration complete!")
        print("\nYou can now run the tests:")
        print("  python test_runner.py")
        
    elif choice == "2":
        create_test_config()
        print("\n⚠ Note: NNTP tests will fail with test config")
        print("  Other components can still be tested")
        
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
