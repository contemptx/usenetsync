#!/usr/bin/env python3
"""
Download real articles from alt.binaries.test on news.newshosting.com
This script shows ACTUAL Usenet server responses and article data.
"""

import socket
import ssl
import time
from datetime import datetime

def send_command(sock, command):
    """Send command to NNTP server"""
    sock.send(f"{command}\r\n".encode())
    
def read_response(sock):
    """Read response from NNTP server"""
    response = b""
    while True:
        chunk = sock.recv(4096)
        response += chunk
        if b"\r\n" in response:
            break
    return response.decode('utf-8', errors='replace').strip()

def read_multiline(sock):
    """Read multiline response ending with ."""
    lines = []
    while True:
        line = b""
        while not line.endswith(b"\r\n"):
            chunk = sock.recv(1)
            if not chunk:
                break
            line += chunk
        
        line = line.decode('utf-8', errors='replace').strip()
        if line == ".":
            break
        if line.startswith(".."):
            line = line[1:]  # Remove dot-stuffing
        lines.append(line)
    return lines

print("="*80)
print("REAL USENET CONNECTION TO news.newshosting.com")
print("="*80)

# Create SSL connection
context = ssl.create_default_context()
sock = socket.create_connection(('news.newshosting.com', 563), timeout=30)
sock = context.wrap_socket(sock, server_hostname='news.newshosting.com')

# Read greeting
greeting = read_response(sock)
print(f"\nServer Greeting: {greeting}")

# Authenticate
print("\nAuthenticating...")
send_command(sock, "AUTHINFO USER contemptx")
auth_user_resp = read_response(sock)
print(f">>> AUTHINFO USER contemptx")
print(f"<<< {auth_user_resp}")

send_command(sock, "AUTHINFO PASS Kia211101#")
auth_pass_resp = read_response(sock)
print(f">>> AUTHINFO PASS ********")
print(f"<<< {auth_pass_resp}")

# Select group
print("\n>>> GROUP alt.binaries.test")
send_command(sock, "GROUP alt.binaries.test")
group_resp = read_response(sock)
print(f"<<< {group_resp}")

# Parse group response
parts = group_resp.split()
if parts[0] == "211":
    count = int(parts[1])
    first = int(parts[2])
    last = int(parts[3])
    
    print(f"\nGroup Statistics:")
    print(f"  Total articles: {count:,}")
    print(f"  First article: {first:,}")
    print(f"  Last article: {last:,}")

# Try to get the last 3 articles
print("\n" + "="*70)
print("DOWNLOADING LAST 3 ACCESSIBLE ARTICLES")
print("="*70)

# Start from the beginning of the group where articles are more likely to exist
articles_found = 0
current = first

while articles_found < 3 and current < first + 100:
    # Try STAT to check if article exists
    print(f"\n>>> STAT {current}")
    send_command(sock, f"STAT {current}")
    stat_resp = read_response(sock)
    print(f"<<< {stat_resp}")
    
    if stat_resp.startswith("223"):  # Article exists
        articles_found += 1
        
        # Get the article
        print(f"\n>>> ARTICLE {current}")
        send_command(sock, f"ARTICLE {current}")
        art_resp = read_response(sock)
        print(f"<<< {art_resp}")
        
        if art_resp.startswith("220"):
            # Read the article
            lines = read_multiline(sock)
            
            print(f"\nARTICLE {articles_found}: #{current}")
            print("-"*60)
            print(f"Total lines: {len(lines)}")
            print("\nFull Article Content:")
            print("-"*60)
            
            for i, line in enumerate(lines):
                print(f"{i+1:4}: {line}")
            
            print("-"*60)
            print("END OF ARTICLE")
            print("-"*60)
    
    current += 1
    
    # Don't hammer the server
    time.sleep(0.1)

# Also try posting and retrieving
print("\n" + "="*70)
print("POSTING A TEST ARTICLE")
print("="*70)

import uuid
unique_id = str(uuid.uuid4())[:8]
message_id = f"<test-{unique_id}@usenet-sync.local>"

print(f"\n>>> POST")
send_command(sock, "POST")
post_resp = read_response(sock)
print(f"<<< {post_resp}")

if post_resp.startswith("340"):  # Send article
    # Build article
    article = f"""From: Test User <test@example.com>
Newsgroups: alt.binaries.test
Subject: Real Test Article {unique_id}
Message-ID: {message_id}
Date: {datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')}
Content-Type: text/plain; charset=UTF-8

This is a REAL article posted to alt.binaries.test
Posted at: {datetime.now().isoformat()}
Unique ID: {unique_id}

Test content:
1. The quick brown fox jumps over the lazy dog
2. Testing special characters: üöä €$¥
3. Numbers: 0123456789
4. Symbols: !@#$%^&*()_+-=[]{{}}|;:,.<>?

End of test article.
.
"""
    
    print(f"\nSending article with Message-ID: {message_id}")
    sock.send(article.replace('\n', '\r\n').encode('utf-8'))
    
    post_result = read_response(sock)
    print(f"<<< {post_result}")
    
    if post_result.startswith("240"):
        print("\n✓ Article posted successfully!")
        
        # Wait and try to retrieve it
        print("\nWaiting 3 seconds for propagation...")
        time.sleep(3)
        
        print(f"\n>>> ARTICLE {message_id}")
        send_command(sock, f"ARTICLE {message_id}")
        retrieve_resp = read_response(sock)
        print(f"<<< {retrieve_resp}")
        
        if retrieve_resp.startswith("220"):
            lines = read_multiline(sock)
            
            print("\n✓✓✓ SUCCESSFULLY RETRIEVED OUR POSTED ARTICLE! ✓✓✓")
            print("="*70)
            print("ARTICLE AS RETRIEVED FROM SERVER:")
            print("="*70)
            
            for i, line in enumerate(lines):
                print(f"{i+1:4}: {line}")
            
            print("="*70)

# Disconnect
print("\n>>> QUIT")
send_command(sock, "QUIT")
quit_resp = read_response(sock)
print(f"<<< {quit_resp}")

sock.close()

print("\n" + "="*80)
print("ALL DATA ABOVE IS REAL FROM news.newshosting.com")
print("="*80)