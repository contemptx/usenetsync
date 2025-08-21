#!/usr/bin/env python3
"""
Setup and manage UsenetSync configuration
Config location: /src/data/config.json
"""

import os
import sys
import json
from pathlib import Path
import getpass

# Add src to path
src_path = os.path.join(os.path.dirname(__file__), 'src')
if os.path.exists(src_path):
    sys.path.insert(0, src_path)
else:
    # We might already be in src
    sys.path.insert(0, os.path.dirname(__file__))

from config.secure_config import NNTPConfig


def setup_configuration():
    """Interactive setup for NewsHosting configuration"""
    print("UsenetSync Configuration Setup")
    print("=" * 50)
    
    config = NNTPConfig()
    
    # Show current config location
    print(f"\nConfiguration file location: {config.config_file}")
    
    # Check if config exists
    if config.config_file.exists():
        print("✓ Configuration file exists")
        with open(config.config_file, 'r') as f:
            current = json.load(f)
        print("\nCurrent configuration:")
        for key, value in current.items():
            if key == 'password':
                continue  # Never show password
            print(f"  {key}: {value}")
    else:
        print("✗ No configuration file found - creating new one")
    
    print("\n" + "-" * 50)
    print("Enter your NewsHosting details (press Enter to keep current value):")
    
    # Get configuration values
    new_config = {
        'host': input(f"NNTP Host [{config.config.get('host', 'news.newshosting.com')}]: ").strip() or config.config.get('host', 'news.newshosting.com'),
        'port': int(input(f"Port [{config.config.get('port', 563)}]: ").strip() or config.config.get('port', 563)),
        'username': input(f"Username [{config.config.get('username', '')}]: ").strip() or config.config.get('username'),
        'use_ssl': True,
        'max_connections': int(input(f"Max connections [{config.config.get('max_connections', 10)}]: ").strip() or config.config.get('max_connections', 10)),
        'timeout': int(input(f"Timeout (seconds) [{config.config.get('timeout', 30)}]: ").strip() or config.config.get('timeout', 30))
    }
    
    # Get password
    password = getpass.getpass("Password: ").strip()
    if password:
        new_config['password'] = password
    
    # Save configuration
    config_dir = config.config_file.parent
    config_dir.mkdir(exist_ok=True)
    
    with open(config.config_file, 'w') as f:
        json.dump(new_config, f, indent=2)
    
    print(f"\n✓ Configuration saved to: {config.config_file}")
    
    # Show how to use
    print("\n" + "=" * 50)
    print("Configuration complete!")
    print("\nYour credentials are saved in the config file.")
    print("\nTo use UsenetSync:")
    print("   from production_nntp_client import ProductionNNTPClient")
    print("   client = ProductionNNTPClient.from_config()")
    
    # Test connection
    if new_config.get('password'):
        test = input("\nTest connection now? (y/n) [y]: ").strip().lower() or 'y'
        if test == 'y':
            # Update the config object
            config.config = new_config
            test_connection()


def test_connection(username=None, password=None):
    """Test the NewsHosting connection"""
    print("\n" + "-" * 50)
    print("Testing NewsHosting connection...")
    
    try:
        from production_nntp_client import ProductionNNTPClient
        
        # Config file should have everything now
        client = ProductionNNTPClient.from_config()
        print(f"✓ Connected to {client.host}:{client.port}")
        
        # Test post
        success, msg_id = client.post_data(
            subject="UsenetSync Configuration Test",
            data=b"This is a test message from UsenetSync configuration",
            newsgroup="alt.binaries.test"
        )
        
        if success:
            print(f"✓ Successfully posted test message!")
            print(f"  Message ID: {msg_id}")
        else:
            print(f"✗ Failed to post: {msg_id}")
        
        client.close()
        
    except Exception as e:
        print(f"✗ Connection failed: {e}")


def show_configuration():
    """Display current configuration"""
    config = NNTPConfig()
    
    print("Current UsenetSync Configuration")
    print("=" * 50)
    print(f"\nConfig file: {config.config_file}")
    
    if config.config_file.exists():
        print("✓ Configuration file exists\n")
        with open(config.config_file, 'r') as f:
            current = json.load(f)
        
        print("Settings:")
        for key, value in current.items():
            print(f"  {key}: {value}")
        
        # Check environment variables
        print("\nEnvironment variables:")
        username_env = os.environ.get('NNTP_USERNAME', 'NOT SET')
        password_env = 'SET' if os.environ.get('NNTP_PASSWORD') else 'NOT SET'
        print(f"  NNTP_USERNAME: {username_env}")
        print(f"  NNTP_PASSWORD: {password_env}")
        
    else:
        print("✗ No configuration file found")
        print("\nRun 'python setup_config.py setup' to create configuration")


def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'setup':
            setup_configuration()
        elif command == 'show':
            show_configuration()
        elif command == 'test':
            test_connection()
        else:
            print(f"Unknown command: {command}")
            print("Usage: python setup_config.py [setup|show|test]")
    else:
        # Default to showing configuration
        show_configuration()
        print("\nCommands:")
        print("  python setup_config.py setup  - Setup/edit configuration")
        print("  python setup_config.py show   - Show current configuration")
        print("  python setup_config.py test   - Test connection")


if __name__ == "__main__":
    main()
