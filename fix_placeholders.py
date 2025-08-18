#!/usr/bin/env python3
"""
Fix all placeholder implementations in the codebase
"""

import os

def fix_server_rotation():
    """Fix server health check simulation"""
    file_path = 'src/networking/server_rotation.py'
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace simulated health check
    content = content.replace(
        "# Simulate health check\n        is_healthy = random.random() > 0.1  # 90% success rate",
        "# Test actual connection\n        try:\n            import socket\n            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n            sock.settimeout(5.0)\n            sock.connect((self.servers.get(server_id).host, self.servers.get(server_id).port))\n            sock.close()\n            is_healthy = True\n        except:\n            is_healthy = False"
    )
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("✅ Fixed server health check")

def fix_cli_download():
    """Fix CLI download mock"""
    file_path = 'src/cli.py'
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace mock download
    content = content.replace(
        '# Start download (mock for now)\n        print(json.dumps({"status": "success", "message": "Download started"}))',
        '# Start actual download\n        import asyncio\n        loop = asyncio.new_event_loop()\n        success = loop.run_until_complete(download_system.download_file(share_id, destination))\n        loop.close()\n        if success:\n            print(json.dumps({"status": "success", "message": f"Downloaded to {destination}"}))\n        else:\n            print(json.dumps({"status": "error", "message": "Download failed"}), file=sys.stderr)\n            sys.exit(1)'
    )
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("✅ Fixed CLI download")

if __name__ == "__main__":
    print("Fixing placeholders...")
    fix_server_rotation()
    fix_cli_download()
    print("✅ Done!")
